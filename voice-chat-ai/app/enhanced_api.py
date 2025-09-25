"""
Enhanced API Endpoints for AI Interviewer Bot
Integrates RAG system, enhanced scoring, and real-time rankings
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
import asyncpg

from .rag_system import CaregiverRAGSystem
from .enhanced_scoring_engine import CaregiverScoringEngine, InterviewEvaluation
from .ranking_engine import CaregiverRankingEngine
from .ml_predictions import CaregiverMLPredictor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/enhanced", tags=["Enhanced Interview System"])

# Request/Response models
class CandidateData(BaseModel):
    firstName: str
    lastName: str
    email: str
    phone: Optional[str] = None
    caregivingExperience: bool = False
    weeklyHours: Optional[int] = 20
    availability: Optional[List[str]] = []
    languages: Optional[List[str]] = []

class QuestionResponse(BaseModel):
    question_id: str
    question_text: str
    candidate_answer: str
    transcription_confidence: Optional[float] = 1.0
    response_time_seconds: Optional[float] = None

class InterviewSubmission(BaseModel):
    userData: CandidateData
    conversationHistory: List[Dict]
    sessionId: Optional[str] = None

class RankingQuery(BaseModel):
    page: int = 1
    per_page: int = 20
    tier: Optional[str] = None
    min_score: Optional[float] = None
    sort_by: str = "rank"

# Global components (initialized at startup)
rag_system: Optional[CaregiverRAGSystem] = None
scoring_engine: Optional[CaregiverScoringEngine] = None
ranking_engine: Optional[CaregiverRankingEngine] = None
ml_predictor: Optional[CaregiverMLPredictor] = None

async def initialize_enhanced_system():
    """Initialize all enhanced system components"""
    global rag_system, scoring_engine, ranking_engine, ml_predictor
    
    try:
        # Database connections
        db_connection = os.getenv('DATABASE_URL', 'postgresql://interview_admin:secure_password@localhost:5432/interview_bot')
        redis_connection = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        elasticsearch_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
        
        # Initialize RAG system with Elasticsearch
        rag_system = CaregiverRAGSystem(db_connection, elasticsearch_url)
        await rag_system.initialize_expected_answers()
        
        # Initialize scoring engine
        scoring_engine = CaregiverScoringEngine(db_connection, rag_system)
        
        # Initialize ranking engine
        ranking_engine = CaregiverRankingEngine(db_connection, redis_connection)
        await ranking_engine.initialize_redis()
        
        # Initialize ML predictor
        ml_predictor = CaregiverMLPredictor(db_connection)
        await ml_predictor.load_models()
        
        logger.info("Enhanced system components initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing enhanced system: {e}")
        raise

@router.post("/evaluate_interview")
async def evaluate_interview_enhanced(submission: InterviewSubmission, background_tasks: BackgroundTasks):
    """Enhanced interview evaluation with RAG and ML predictions"""
    try:
        if not all([rag_system, scoring_engine, ranking_engine, ml_predictor]):
            raise HTTPException(status_code=500, detail="Enhanced system not initialized")
        
        # Store candidate
        candidate_id = await _store_candidate(submission.userData)
        
        # Create interview session
        session_id = await _create_interview_session(candidate_id, submission.userData)
        
        # Extract question responses from conversation history
        question_responses = _extract_question_responses(submission.conversationHistory)
        
        # Evaluate interview using enhanced scoring
        evaluation = await scoring_engine.evaluate_complete_interview(
            candidate_id, session_id, question_responses
        )
        
        # Store evaluation results
        await scoring_engine.store_evaluation_results(evaluation)
        
        # Get ML predictions
        candidate_features = _prepare_candidate_features(evaluation, submission.userData)
        ml_prediction = await ml_predictor.predict_hiring_success(candidate_features)
        
        # Update rankings (background task for performance)
        background_tasks.add_task(_update_rankings_background, evaluation, ml_prediction)
        
        # Prepare response
        response = {
            "status": "success",
            "candidate_id": candidate_id,
            "session_id": session_id,
            "evaluation": {
                "dimension_scores": {
                    "experience": evaluation.experience_avg,
                    "motivation": evaluation.motivation_score,
                    "punctuality": evaluation.punctuality_avg,
                    "empathy": evaluation.empathy_avg,
                    "communication": evaluation.communication_score
                },
                "total_score": evaluation.total_weighted_score,
                "recommendation": evaluation.recommendation,
                "confidence_level": evaluation.confidence_level,
                "consistency_factor": evaluation.consistency_factor,
                "strengths": evaluation.strengths,
                "areas_for_improvement": evaluation.areas_for_improvement
            },
            "ml_predictions": {
                "hiring_probability": ml_prediction.hiring_probability,
                "expected_performance": ml_prediction.expected_performance,
                "risk_factors": ml_prediction.risk_factors,
                "confidence_level": ml_prediction.confidence_level,
                "similar_candidates": {
                    "hired": ml_prediction.similar_candidates_hired,
                    "total": ml_prediction.similar_candidates_total
                }
            },
            "question_details": [
                {
                    "question_id": qs.question_id,
                    "final_score": qs.final_score,
                    "rag_similarity": qs.rag_evaluation.semantic_similarity_score,
                    "rag_quality": qs.rag_evaluation.best_match.quality_level,
                    "empathy_bonus": qs.rag_evaluation.empathy_bonus,
                    "patient_story_bonus": qs.rag_evaluation.patient_story_bonus
                }
                for qs in evaluation.question_scores
            ]
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in enhanced interview evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation error: {str(e)}")

@router.get("/rankings")
async def get_rankings(query: RankingQuery):
    """Get candidate rankings with filtering and pagination"""
    try:
        if not ranking_engine:
            raise HTTPException(status_code=500, detail="Ranking engine not initialized")
        
        # Get candidates by tier if specified
        if query.tier:
            candidates = await ranking_engine.get_candidates_by_tier(query.tier, query.per_page * 2)
        else:
            candidates = await ranking_engine.get_live_leaderboard(query.per_page * 2)
        
        # Apply additional filtering
        if query.min_score:
            candidates = [c for c in candidates if c.total_weighted_score >= query.min_score]
        
        # Apply pagination
        start_idx = (query.page - 1) * query.per_page
        end_idx = start_idx + query.per_page
        paginated_candidates = candidates[start_idx:end_idx]
        
        return {
            "status": "success",
            "candidates": [
                {
                    "candidate_id": c.candidate_id,
                    "name": c.candidate_name,
                    "rank": c.overall_rank,
                    "percentile": c.percentile_rank,
                    "tier": c.tier,
                    "total_score": c.total_weighted_score,
                    "dimension_scores": c.dimension_scores,
                    "hiring_probability": c.hiring_probability,
                    "expected_performance": c.expected_performance,
                    "risk_factors": c.risk_factors,
                    "confidence_level": c.confidence_level,
                    "interview_date": c.interview_date.isoformat() if c.interview_date else None
                }
                for c in paginated_candidates
            ],
            "pagination": {
                "page": query.page,
                "per_page": query.per_page,
                "total": len(candidates),
                "pages": (len(candidates) + query.per_page - 1) // query.per_page
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting rankings: {e}")
        raise HTTPException(status_code=500, detail=f"Rankings error: {str(e)}")

@router.get("/candidate/{candidate_id}")
async def get_candidate_details(candidate_id: str):
    """Get detailed information for a specific candidate"""
    try:
        if not ranking_engine:
            raise HTTPException(status_code=500, detail="Ranking engine not initialized")
        
        candidate_details = await ranking_engine.get_candidate_details(candidate_id)
        
        if not candidate_details:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Get cohort analysis
        cohort_analysis = await ranking_engine.get_cohort_analysis(candidate_id)
        
        response = {
            "status": "success",
            **candidate_details
        }
        
        if cohort_analysis:
            response["cohort_analysis"] = {
                "cohort_size": cohort_analysis.cohort_size,
                "cohort_mean_score": cohort_analysis.cohort_mean_score,
                "candidate_z_score": cohort_analysis.candidate_z_score,
                "cohort_percentile": cohort_analysis.cohort_percentile,
                "performance_vs_cohort": cohort_analysis.performance_vs_cohort
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate details: {e}")
        raise HTTPException(status_code=500, detail=f"Details error: {str(e)}")

@router.get("/analytics/dashboard")
async def get_dashboard_analytics():
    """Get comprehensive dashboard analytics"""
    try:
        if not ranking_engine:
            raise HTTPException(status_code=500, detail="Ranking engine not initialized")
        
        # Get ranking analytics
        ranking_analytics = await ranking_engine.get_ranking_analytics(30)
        
        # Get RAG analytics
        rag_analytics = await rag_system.get_rag_analytics(30) if rag_system else {}
        
        # Get ML model performance
        ml_performance = await ml_predictor.get_model_performance_report() if ml_predictor else {}
        
        return {
            "status": "success",
            "ranking_analytics": ranking_analytics,
            "rag_analytics": rag_analytics,
            "ml_performance": ml_performance,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@router.post("/admin/update_outcome")
async def update_hiring_outcome(request: Request):
    """Update actual hiring outcome for ML model training"""
    try:
        data = await request.json()
        candidate_id = data.get('candidate_id')
        hired = data.get('hired')
        performance_rating = data.get('performance_rating')
        
        if not candidate_id or hired is None:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        if not ml_predictor:
            raise HTTPException(status_code=500, detail="ML predictor not initialized")
        
        # Update ML model with outcome
        await ml_predictor.update_model_with_outcome(candidate_id, hired, performance_rating)
        
        return {
            "status": "success",
            "message": f"Updated outcome for candidate {candidate_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating hiring outcome: {e}")
        raise HTTPException(status_code=500, detail=f"Update error: {str(e)}")

@router.post("/admin/add_expected_answer")
async def add_expected_answer(request: Request):
    """Add new expected answer for RAG system"""
    try:
        data = await request.json()
        question_id = data.get('question_id')
        answer_text = data.get('answer_text')
        quality_level = data.get('quality_level')
        empathy_indicators = data.get('empathy_indicators', [])
        experience_indicators = data.get('experience_indicators', [])
        behavioral_patterns = data.get('behavioral_patterns', [])
        
        if not all([question_id, answer_text, quality_level]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        if not rag_system:
            raise HTTPException(status_code=500, detail="RAG system not initialized")
        
        # Add expected answer
        answer_id = await rag_system.add_expected_answer(
            question_id, answer_text, quality_level,
            empathy_indicators, experience_indicators, behavioral_patterns
        )
        
        return {
            "status": "success",
            "answer_id": answer_id,
            "message": f"Added expected answer for {question_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding expected answer: {e}")
        raise HTTPException(status_code=500, detail=f"Add answer error: {str(e)}")

# Helper functions
async def _store_candidate(candidate_data: CandidateData) -> str:
    """Store candidate in database"""
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        
        candidate_id = await conn.fetchval("""
            INSERT INTO candidates (
                first_name, last_name, email, phone, caregiving_experience,
                weekly_hours, availability, languages, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """,
        candidate_data.firstName, candidate_data.lastName, candidate_data.email,
        candidate_data.phone, candidate_data.caregivingExperience,
        candidate_data.weeklyHours, json.dumps(candidate_data.availability),
        json.dumps(candidate_data.languages), json.dumps(candidate_data.dict()))
        
        await conn.close()
        return str(candidate_id)
        
    except Exception as e:
        logger.error(f"Error storing candidate: {e}")
        raise

async def _create_interview_session(candidate_id: str, candidate_data: CandidateData) -> str:
    """Create interview session"""
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        
        session_id = await conn.fetchval("""
            INSERT INTO interview_sessions (candidate_id, metadata)
            VALUES ($1, $2)
            RETURNING id
        """, candidate_id, json.dumps({"candidate_data": candidate_data.dict()}))
        
        await conn.close()
        return str(session_id)
        
    except Exception as e:
        logger.error(f"Error creating interview session: {e}")
        raise

def _extract_question_responses(conversation_history: List[Dict]) -> List[Dict]:
    """Extract question responses from conversation history"""
    question_responses = []
    
    # Map conversation to questions (simplified - you may need to adjust based on your format)
    question_texts = {
        'Q1': 'Have you ever worked as a caregiver? If so, can you please share what kind of patients/customers you worked with and what services / activities you performed?',
        'Q2': 'Imagine that you\'re finding a caregiver for one of your loved ones. What traits or skills would be most important to you for this caregiver to have?',
        'Q3': 'Describe for me how your prior work or life experience has helped you build the skills necessary to be a good caregiver?',
        'Q4': 'Why do you want to be a caregiver? What are the most rewarding aspects of the job?',
        'Q5': 'Tell me about a time when being late caused problems for you or your team. What did you learn from it?',
        'Q6': 'Have you ever had to adjust your routine to ensure punctuality at work? What changes did you make?',
        'Q7': 'Tell me about a time when you cared for a senior. What part of the experience was most difficult and what was most meaningful to you?',
        'Q8': 'Tell me about a time when you helped a colleague or client who was struggling emotionally or professionally. What did you do?',
        'Q9': 'If we were to ask your co-workers about you, what are the three things they would say?'
    }
    
    # Extract user responses (assuming they alternate with bot questions)
    user_responses = [msg for msg in conversation_history if msg.get('role') == 'user']
    
    for i, response in enumerate(user_responses[:9]):  # Limit to 9 questions
        question_id = f'Q{i+1}'
        question_responses.append({
            'question_id': question_id,
            'question_text': question_texts.get(question_id, 'Question not found'),
            'candidate_answer': response.get('content', ''),
            'transcription_confidence': response.get('confidence', 1.0)
        })
    
    return question_responses

def _prepare_candidate_features(evaluation: InterviewEvaluation, candidate_data: CandidateData) -> Dict:
    """Prepare features for ML prediction"""
    return {
        'experience_avg': evaluation.experience_avg,
        'motivation_score': evaluation.motivation_score,
        'punctuality_avg': evaluation.punctuality_avg,
        'empathy_avg': evaluation.empathy_avg,
        'communication_score': evaluation.communication_score,
        'consistency_factor': evaluation.consistency_factor,
        'overall_quality_factor': evaluation.overall_quality_factor,
        'avg_empathy_bonus': np.mean([qs.rag_evaluation.empathy_bonus for qs in evaluation.question_scores]),
        'avg_patient_story_bonus': np.mean([qs.rag_evaluation.patient_story_bonus for qs in evaluation.question_scores]),
        'caregiving_experience': candidate_data.caregivingExperience,
        'weekly_hours': candidate_data.weeklyHours or 20
    }

async def _update_rankings_background(evaluation: InterviewEvaluation, ml_prediction):
    """Background task to update rankings"""
    try:
        # Update candidate ranking
        await ranking_engine.update_candidate_ranking(evaluation)
        
        # Store ML predictions
        await _store_ml_predictions(evaluation.candidate_id, ml_prediction)
        
        logger.info(f"Background ranking update completed for {evaluation.candidate_id}")
        
    except Exception as e:
        logger.error(f"Error in background ranking update: {e}")

async def _store_ml_predictions(candidate_id: str, ml_prediction):
    """Store ML predictions in database"""
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        
        await conn.execute("""
            UPDATE candidate_rankings SET
                hiring_probability = $2,
                expected_performance = $3,
                risk_factors = $4,
                last_updated = NOW()
            WHERE candidate_id = $1
        """, candidate_id, ml_prediction.hiring_probability, ml_prediction.expected_performance,
        json.dumps(ml_prediction.risk_factors))
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error storing ML predictions: {e}")

# Additional utility endpoints
@router.get("/system/health")
async def system_health_check():
    """Check health of all system components"""
    health_status = {
        "rag_system": rag_system is not None,
        "scoring_engine": scoring_engine is not None,
        "ranking_engine": ranking_engine is not None,
        "ml_predictor": ml_predictor is not None,
        "timestamp": datetime.now().isoformat()
    }
    
    # Test database connections
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        await conn.fetchval("SELECT 1")
        await conn.close()
        health_status["database"] = True
    except:
        health_status["database"] = False
    
    # Test Redis connection
    try:
        if ranking_engine and ranking_engine.redis_client:
            await ranking_engine.redis_client.ping()
            health_status["redis"] = True
        else:
            health_status["redis"] = False
    except:
        health_status["redis"] = False
    
    overall_health = all([
        health_status["rag_system"],
        health_status["scoring_engine"], 
        health_status["ranking_engine"],
        health_status["ml_predictor"],
        health_status["database"],
        health_status["redis"]
    ])
    
    return {
        "status": "healthy" if overall_health else "degraded",
        "components": health_status
    }

@router.get("/system/stats")
async def get_system_statistics():
    """Get system usage statistics"""
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(DISTINCT c.id) as total_candidates,
                COUNT(DISTINCT is.id) as total_interviews,
                COUNT(DISTINCT CASE WHEN is.session_status = 'completed' THEN is.id END) as completed_interviews,
                AVG(CASE WHEN is.session_status = 'completed' THEN is.total_score END) as avg_score,
                COUNT(DISTINCT CASE WHEN is.completed_at >= NOW() - INTERVAL '24 hours' THEN is.id END) as interviews_last_24h
            FROM candidates c
            LEFT JOIN interview_sessions is ON c.id = is.candidate_id
        """)
        
        await conn.close()
        
        return {
            "status": "success",
            "statistics": {
                "total_candidates": stats['total_candidates'],
                "total_interviews": stats['total_interviews'],
                "completed_interviews": stats['completed_interviews'],
                "completion_rate": (stats['completed_interviews'] / stats['total_interviews'] * 100) if stats['total_interviews'] > 0 else 0,
                "average_score": float(stats['avg_score'] or 0),
                "interviews_last_24h": stats['interviews_last_24h']
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Statistics error: {str(e)}")

# Import numpy for helper functions
import numpy as np
