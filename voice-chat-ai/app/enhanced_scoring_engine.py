"""
Enhanced Scoring Engine for Caregiver Interviews
Integrates RAG system with multi-dimensional scoring and contextual adjustments
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncpg
import numpy as np
from textblob import TextBlob

from .rag_system import CaregiverRAGSystem, RAGEvaluationResult

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QuestionScore:
    """Individual question scoring result"""
    question_id: str
    question_text: str
    candidate_answer: str
    
    # Multi-dimensional scores
    semantic_similarity_score: float
    completeness_score: float
    empathy_score: float
    behavioral_score: float
    
    # RAG results
    rag_evaluation: RAGEvaluationResult
    
    # Final scores
    base_score: float
    adjusted_score: float
    final_score: float
    
    # Metadata
    transcription_confidence: float
    response_time_seconds: Optional[float]
    word_count: int

@dataclass
class InterviewEvaluation:
    """Complete interview evaluation result"""
    candidate_id: str
    session_id: str
    question_scores: List[QuestionScore]
    
    # Dimension averages
    experience_avg: float
    motivation_score: float
    punctuality_avg: float
    empathy_avg: float
    communication_score: float
    
    # Final results
    total_weighted_score: float
    recommendation: str  # 'hire', 'consider', 'reject'
    confidence_level: str
    
    # Analytics
    consistency_factor: float
    overall_quality_factor: float
    strengths: List[str]
    areas_for_improvement: List[str]

class CaregiverScoringEngine:
    """Enhanced scoring engine for caregiver interviews"""
    
    def __init__(self, db_connection_string: str, rag_system: CaregiverRAGSystem):
        self.db_connection_string = db_connection_string
        self.rag_system = rag_system
        
        # Question mapping to dimensions
        self.question_mapping = {
            'Q1': 'experience',  # Caregiver Experience
            'Q2': 'experience',  # Ideal Caregiver Traits
            'Q3': 'experience',  # Experience Building Skills
            'Q4': 'motivation',  # Why Caregiver & Rewards
            'Q5': 'punctuality', # Punctuality Problems
            'Q6': 'punctuality', # Routine Adjustment
            'Q7': 'empathy',     # Senior Care Experience
            'Q8': 'empathy',     # Emotional Support
            'Q9': 'communication' # Coworker Perspective
        }
        
        # Load system configuration
        self.config = {}
        asyncio.create_task(self._load_configuration())
        
        logger.info("CaregiverScoringEngine initialized")
    
    async def _load_configuration(self):
        """Load system configuration from database"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            config_rows = await conn.fetch("SELECT config_key, config_value FROM system_config")
            
            for row in config_rows:
                self.config[row['config_key']] = row['config_value']
            
            await conn.close()
            logger.info("System configuration loaded")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Use default configuration
            self.config = {
                'question_weights': {
                    'experience': 0.30, 'motivation': 0.20, 'punctuality': 0.15,
                    'empathy': 0.25, 'communication': 0.10
                },
                'caregiver_bonuses': {
                    'empathy_bonus': 1.12, 'patient_story_bonus': 1.08,
                    'care_experience_bonus': 1.05, 'dignity_mention_bonus': 1.05
                }
            }
    
    async def evaluate_question_response(self, question_id: str, question_text: str,
                                       candidate_answer: str, transcription_confidence: float = 1.0,
                                       response_time_seconds: Optional[float] = None) -> QuestionScore:
        """
        Evaluate a single question response with multi-dimensional scoring
        
        Args:
            question_id: Question identifier (Q1, Q2, etc.)
            question_text: The actual question text
            candidate_answer: Candidate's response
            transcription_confidence: Confidence of speech-to-text (0-1)
            response_time_seconds: Time taken to respond
            
        Returns:
            QuestionScore with complete evaluation
        """
        try:
            # Get RAG evaluation
            rag_result = await self.rag_system.evaluate_answer(question_id, candidate_answer)
            
            # Calculate multi-dimensional scores
            semantic_score = rag_result.semantic_similarity_score
            completeness_score = self._calculate_completeness_score(candidate_answer, question_id)
            empathy_score = self._calculate_empathy_score(candidate_answer, rag_result)
            behavioral_score = self._calculate_behavioral_score(candidate_answer, question_id)
            
            # Calculate base score (weighted average of dimensions)
            dimension_weights = self._get_question_dimension_weights(question_id)
            base_score = (
                semantic_score * dimension_weights.get('semantic', 0.4) +
                completeness_score * dimension_weights.get('completeness', 0.3) +
                empathy_score * dimension_weights.get('empathy', 0.2) +
                behavioral_score * dimension_weights.get('behavioral', 0.1)
            )
            
            # Apply contextual adjustments
            adjusted_score = self._apply_contextual_adjustments(
                base_score, candidate_answer, transcription_confidence, response_time_seconds
            )
            
            # Use RAG final score as the authoritative final score
            final_score = rag_result.final_score
            
            # Calculate word count
            word_count = len(candidate_answer.split())
            
            return QuestionScore(
                question_id=question_id,
                question_text=question_text,
                candidate_answer=candidate_answer,
                semantic_similarity_score=semantic_score,
                completeness_score=completeness_score,
                empathy_score=empathy_score,
                behavioral_score=behavioral_score,
                rag_evaluation=rag_result,
                base_score=base_score,
                adjusted_score=adjusted_score,
                final_score=final_score,
                transcription_confidence=transcription_confidence,
                response_time_seconds=response_time_seconds,
                word_count=word_count
            )
            
        except Exception as e:
            logger.error(f"Error evaluating question {question_id}: {e}")
            # Return default score on error
            return self._create_default_question_score(question_id, question_text, candidate_answer)
    
    async def evaluate_complete_interview(self, candidate_id: str, session_id: str,
                                        question_responses: List[Dict]) -> InterviewEvaluation:
        """
        Evaluate complete interview with all questions
        
        Args:
            candidate_id: Candidate identifier
            session_id: Interview session identifier
            question_responses: List of question response dictionaries
            
        Returns:
            InterviewEvaluation with complete assessment
        """
        try:
            # Score each question
            question_scores = []
            for response in question_responses:
                question_score = await self.evaluate_question_response(
                    response['question_id'],
                    response['question_text'],
                    response['candidate_answer'],
                    response.get('transcription_confidence', 1.0),
                    response.get('response_time_seconds')
                )
                question_scores.append(question_score)
            
            # Calculate dimension averages
            dimension_scores = self._calculate_dimension_scores(question_scores)
            
            # Calculate weighted total score
            weights = self.config.get('question_weights', {})
            total_weighted_score = (
                dimension_scores['experience'] * weights.get('experience', 0.30) +
                dimension_scores['motivation'] * weights.get('motivation', 0.20) +
                dimension_scores['punctuality'] * weights.get('punctuality', 0.15) +
                dimension_scores['empathy'] * weights.get('empathy', 0.25) +
                dimension_scores['communication'] * weights.get('communication', 0.10)
            )
            
            # Calculate consistency factor
            consistency_factor = self._calculate_consistency_factor(question_scores)
            
            # Calculate overall quality factor
            quality_factor = self._calculate_overall_quality_factor(question_scores)
            
            # Determine recommendation
            recommendation = self._determine_recommendation(total_weighted_score, dimension_scores)
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(question_scores)
            
            # Identify strengths and areas for improvement
            strengths, areas_for_improvement = self._analyze_performance(dimension_scores, question_scores)
            
            return InterviewEvaluation(
                candidate_id=candidate_id,
                session_id=session_id,
                question_scores=question_scores,
                experience_avg=dimension_scores['experience'],
                motivation_score=dimension_scores['motivation'],
                punctuality_avg=dimension_scores['punctuality'],
                empathy_avg=dimension_scores['empathy'],
                communication_score=dimension_scores['communication'],
                total_weighted_score=total_weighted_score,
                recommendation=recommendation,
                confidence_level=confidence_level,
                consistency_factor=consistency_factor,
                overall_quality_factor=quality_factor,
                strengths=strengths,
                areas_for_improvement=areas_for_improvement
            )
            
        except Exception as e:
            logger.error(f"Error evaluating complete interview: {e}")
            raise
    
    async def store_evaluation_results(self, evaluation: InterviewEvaluation):
        """Store evaluation results in database"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Store question responses
            for question_score in evaluation.question_scores:
                await conn.execute("""
                    INSERT INTO question_responses (
                        session_id, question_id, question_text, candidate_answer,
                        transcription_confidence, semantic_similarity_score,
                        completeness_score, empathy_score, behavioral_score,
                        rag_best_match_score, rag_match_quality, expected_answer_id,
                        empathy_bonus, patient_story_bonus, care_experience_bonus,
                        dignity_mention_bonus, final_question_score
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                """, 
                evaluation.session_id, question_score.question_id, question_score.question_text,
                question_score.candidate_answer, question_score.transcription_confidence,
                question_score.semantic_similarity_score, question_score.completeness_score,
                question_score.empathy_score, question_score.behavioral_score,
                question_score.rag_evaluation.best_match.similarity_score,
                question_score.rag_evaluation.best_match.quality_level,
                question_score.rag_evaluation.best_match.answer_id,
                question_score.rag_evaluation.empathy_bonus,
                question_score.rag_evaluation.patient_story_bonus,
                question_score.rag_evaluation.care_experience_bonus,
                question_score.rag_evaluation.dignity_mention_bonus,
                question_score.final_score)
            
            # Update interview session
            await conn.execute("""
                UPDATE interview_sessions SET
                    session_status = 'completed',
                    completed_at = NOW(),
                    total_score = $2,
                    recommendation = $3,
                    experience_avg = $4,
                    motivation_score = $5,
                    punctuality_avg = $6,
                    empathy_avg = $7,
                    communication_score = $8
                WHERE id = $1
            """, 
            evaluation.session_id, evaluation.total_weighted_score, evaluation.recommendation,
            evaluation.experience_avg, evaluation.motivation_score, evaluation.punctuality_avg,
            evaluation.empathy_avg, evaluation.communication_score)
            
            await conn.close()
            logger.info(f"Stored evaluation results for session {evaluation.session_id}")
            
        except Exception as e:
            logger.error(f"Error storing evaluation results: {e}")
            raise
    
    def _calculate_completeness_score(self, answer: str, question_id: str) -> float:
        """Calculate completeness score based on answer length and content"""
        word_count = len(answer.split())
        
        # Expected word counts by question type
        expected_ranges = {
            'Q1': (30, 100),   # Experience questions need detail
            'Q2': (20, 80),    # Trait questions
            'Q3': (30, 100),   # Skill building
            'Q4': (25, 90),    # Motivation
            'Q5': (20, 70),    # Punctuality stories
            'Q6': (15, 60),    # Routine adjustments
            'Q7': (40, 120),   # Senior care stories (most detailed)
            'Q8': (30, 100),   # Emotional support
            'Q9': (15, 60)     # Coworker feedback
        }
        
        min_words, max_words = expected_ranges.get(question_id, (20, 80))
        
        if word_count < min_words:
            return max(30, (word_count / min_words) * 70)  # Penalty for too short
        elif word_count > max_words * 1.5:
            return 85  # Slight penalty for too long
        elif min_words <= word_count <= max_words:
            return 95  # Optimal length
        else:
            return 90  # Slightly long but acceptable
    
    def _calculate_empathy_score(self, answer: str, rag_result: RAGEvaluationResult) -> float:
        """Calculate empathy score using sentiment analysis and RAG bonuses"""
        # Use TextBlob for sentiment analysis
        blob = TextBlob(answer)
        sentiment_score = (blob.sentiment.polarity + 1) * 50  # Convert -1,1 to 0,100
        
        # Combine with RAG empathy indicators
        empathy_multiplier = rag_result.empathy_bonus
        
        # Base empathy score from sentiment and RAG
        base_empathy = min(sentiment_score * empathy_multiplier, 100)
        
        # Additional empathy indicators
        empathy_phrases = [
            "understand", "feel", "comfort", "support", "listen", "care about",
            "important to", "respect", "dignity", "person", "individual"
        ]
        
        answer_lower = answer.lower()
        phrase_count = sum(1 for phrase in empathy_phrases if phrase in answer_lower)
        
        # Bonus for empathy phrases
        phrase_bonus = min(phrase_count * 5, 20)  # Up to 20 points bonus
        
        return min(base_empathy + phrase_bonus, 100)
    
    def _calculate_behavioral_score(self, answer: str, question_id: str) -> float:
        """Calculate behavioral score using STAR method detection"""
        answer_lower = answer.lower()
        
        # STAR method indicators
        situation_indicators = ["when", "time", "situation", "experience", "worked", "was"]
        task_indicators = ["needed to", "had to", "responsible", "task", "job", "role"]
        action_indicators = ["i did", "i used", "i tried", "i learned", "i helped", "i made"]
        result_indicators = ["result", "outcome", "learned", "improved", "helped", "successful"]
        
        star_scores = {
            'situation': sum(1 for ind in situation_indicators if ind in answer_lower),
            'task': sum(1 for ind in task_indicators if ind in answer_lower),
            'action': sum(1 for ind in action_indicators if ind in answer_lower),
            'result': sum(1 for ind in result_indicators if ind in answer_lower)
        }
        
        # Score based on STAR completeness
        star_present = sum(1 for score in star_scores.values() if score > 0)
        
        if star_present >= 3:
            return 90  # Good STAR structure
        elif star_present >= 2:
            return 75  # Partial STAR
        elif star_present >= 1:
            return 60  # Some structure
        else:
            return 50  # Minimal structure
    
    def _get_question_dimension_weights(self, question_id: str) -> Dict[str, float]:
        """Get dimension weights for specific question types"""
        # Empathy questions weight empathy more heavily
        if question_id in ['Q7', 'Q8']:
            return {'semantic': 0.3, 'completeness': 0.2, 'empathy': 0.4, 'behavioral': 0.1}
        # Experience questions weight semantic and behavioral more
        elif question_id in ['Q1', 'Q2', 'Q3']:
            return {'semantic': 0.4, 'completeness': 0.3, 'empathy': 0.1, 'behavioral': 0.2}
        # Default weights
        else:
            return {'semantic': 0.4, 'completeness': 0.3, 'empathy': 0.2, 'behavioral': 0.1}
    
    def _apply_contextual_adjustments(self, base_score: float, answer: str,
                                    transcription_confidence: float,
                                    response_time: Optional[float]) -> float:
        """Apply contextual adjustments to base score"""
        adjusted_score = base_score
        
        # Transcription confidence adjustment
        if transcription_confidence < 0.8:
            adjusted_score *= 0.95  # 5% penalty for low confidence
        
        # Response time adjustment (if available)
        if response_time:
            if response_time < 10:  # Too quick, might be shallow
                adjusted_score *= 0.98
            elif response_time > 120:  # Too long, might indicate confusion
                adjusted_score *= 0.97
        
        # Answer length adjustment
        word_count = len(answer.split())
        if word_count < 10:  # Too short
            adjusted_score *= 0.9
        elif word_count > 200:  # Too long
            adjusted_score *= 0.95
        
        return min(adjusted_score, 100)
    
    def _calculate_dimension_scores(self, question_scores: List[QuestionScore]) -> Dict[str, float]:
        """Calculate average scores for each dimension"""
        dimension_scores = {
            'experience': [],
            'motivation': [],
            'punctuality': [],
            'empathy': [],
            'communication': []
        }
        
        for score in question_scores:
            dimension = self.question_mapping.get(score.question_id)
            if dimension:
                dimension_scores[dimension].append(score.final_score)
        
        # Calculate averages
        return {
            dimension: sum(scores) / len(scores) if scores else 0
            for dimension, scores in dimension_scores.items()
        }
    
    def _calculate_consistency_factor(self, question_scores: List[QuestionScore]) -> float:
        """Calculate consistency factor across all questions"""
        scores = [qs.final_score for qs in question_scores]
        if len(scores) < 2:
            return 1.0
        
        std_dev = np.std(scores)
        mean_score = np.mean(scores)
        
        # Coefficient of variation
        cv = std_dev / mean_score if mean_score > 0 else 0
        
        # Lower CV = higher consistency
        if cv <= 0.15:
            return 1.05  # 5% bonus for very consistent
        elif cv <= 0.25:
            return 1.0   # No adjustment
        else:
            return max(0.95, 1 - (cv - 0.25))  # Penalty for inconsistency
    
    def _calculate_overall_quality_factor(self, question_scores: List[QuestionScore]) -> float:
        """Calculate overall quality factor based on response quality"""
        quality_indicators = []
        
        for qs in question_scores:
            # High RAG similarity indicates quality
            if qs.rag_evaluation.best_match.similarity_score > 0.85:
                quality_indicators.append(1.1)
            elif qs.rag_evaluation.best_match.similarity_score > 0.75:
                quality_indicators.append(1.05)
            else:
                quality_indicators.append(1.0)
        
        return sum(quality_indicators) / len(quality_indicators) if quality_indicators else 1.0
    
    def _determine_recommendation(self, total_score: float, dimension_scores: Dict[str, float]) -> str:
        """Determine hiring recommendation based on scores"""
        # Check for critical failures in key dimensions
        if dimension_scores['empathy'] < 60:  # Critical for caregivers
            return 'reject'
        if dimension_scores['experience'] < 50:  # Need some experience
            return 'reject'
        
        # Overall score thresholds
        if total_score >= 85:
            return 'hire'
        elif total_score >= 70:
            return 'consider'
        else:
            return 'reject'
    
    def _calculate_confidence_level(self, question_scores: List[QuestionScore]) -> str:
        """Calculate confidence level of the evaluation"""
        avg_rag_confidence = np.mean([
            1.0 if qs.rag_evaluation.confidence_level == 'high' else
            0.7 if qs.rag_evaluation.confidence_level == 'medium' else 0.4
            for qs in question_scores
        ])
        
        avg_transcription_confidence = np.mean([
            qs.transcription_confidence for qs in question_scores
        ])
        
        overall_confidence = (avg_rag_confidence + avg_transcription_confidence) / 2
        
        if overall_confidence > 0.8:
            return 'high'
        elif overall_confidence > 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _analyze_performance(self, dimension_scores: Dict[str, float],
                           question_scores: List[QuestionScore]) -> Tuple[List[str], List[str]]:
        """Analyze performance to identify strengths and areas for improvement"""
        strengths = []
        areas_for_improvement = []
        
        # Analyze dimension scores
        for dimension, score in dimension_scores.items():
            if score >= 85:
                strengths.append(f"Strong {dimension} demonstrated")
            elif score < 65:
                areas_for_improvement.append(f"Improve {dimension} responses")
        
        # Analyze specific patterns
        empathy_bonuses = [qs.rag_evaluation.empathy_bonus for qs in question_scores]
        avg_empathy_bonus = np.mean(empathy_bonuses)
        
        if avg_empathy_bonus > 1.05:
            strengths.append("Consistent empathy and compassion shown")
        
        patient_story_bonuses = [qs.rag_evaluation.patient_story_bonus for qs in question_scores]
        avg_story_bonus = np.mean(patient_story_bonuses)
        
        if avg_story_bonus > 1.03:
            strengths.append("Good use of specific patient care examples")
        
        return strengths, areas_for_improvement
    
    def _create_default_question_score(self, question_id: str, question_text: str,
                                     candidate_answer: str) -> QuestionScore:
        """Create default question score when evaluation fails"""
        from .rag_system import RAGEvaluationResult, RAGMatch
        
        default_match = RAGMatch(
            answer_id="default", similarity_score=0.5, quality_level="fair",
            score_range_min=50, score_range_max=70, empathy_indicators=[],
            experience_indicators=[], behavioral_patterns=[], answer_text=""
        )
        
        default_rag = RAGEvaluationResult(
            semantic_similarity_score=50.0, best_match=default_match,
            quality_mapping_score=50.0, empathy_bonus=1.0, patient_story_bonus=1.0,
            care_experience_bonus=1.0, dignity_mention_bonus=1.0,
            final_score=50.0, confidence_level="low"
        )
        
        return QuestionScore(
            question_id=question_id, question_text=question_text,
            candidate_answer=candidate_answer, semantic_similarity_score=50.0,
            completeness_score=50.0, empathy_score=50.0, behavioral_score=50.0,
            rag_evaluation=default_rag, base_score=50.0, adjusted_score=50.0,
            final_score=50.0, transcription_confidence=1.0, response_time_seconds=None,
            word_count=len(candidate_answer.split())
        )

# Example usage
async def main():
    """Example usage of the enhanced scoring engine"""
    # Initialize components
    db_connection = "postgresql://interview_admin:secure_password@localhost:5432/interview_bot"
    rag_system = CaregiverRAGSystem(db_connection)
    await rag_system.initialize_expected_answers()
    
    scoring_engine = CaregiverScoringEngine(db_connection, rag_system)
    
    # Example question responses
    test_responses = [
        {
            'question_id': 'Q7',
            'question_text': 'Tell me about a time when you cared for a senior. What was most difficult and meaningful?',
            'candidate_answer': 'I took care of my grandmother with dementia for two years. The hardest part was her confusion and agitation. I learned to stay patient and speak calmly. Playing her favorite music helped. The meaningful part was seeing her smile and knowing I was preserving her dignity.',
            'transcription_confidence': 0.95
        }
    ]
    
    # Evaluate single question
    question_score = await scoring_engine.evaluate_question_response(
        test_responses[0]['question_id'],
        test_responses[0]['question_text'],
        test_responses[0]['candidate_answer'],
        test_responses[0]['transcription_confidence']
    )
    
    print(f"Question {question_score.question_id} Final Score: {question_score.final_score:.1f}/100")
    print(f"Empathy Bonus: {question_score.rag_evaluation.empathy_bonus:.2f}x")
    print(f"RAG Match Quality: {question_score.rag_evaluation.best_match.quality_level}")

if __name__ == "__main__":
    asyncio.run(main())
