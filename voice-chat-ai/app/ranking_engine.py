"""
Real-Time Ranking Engine for Caregiver Interviews
Handles candidate rankings, tier classification, and comparative analysis
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncpg
import redis.asyncio as redis
import numpy as np

from .enhanced_scoring_engine import InterviewEvaluation

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CandidateRanking:
    """Candidate ranking information"""
    candidate_id: str
    candidate_name: str
    overall_rank: int
    percentile_rank: float
    tier: str
    total_weighted_score: float
    dimension_scores: Dict[str, float]
    hiring_probability: float
    expected_performance: float
    risk_factors: List[str]
    confidence_level: str
    interview_date: datetime

@dataclass
class CohortAnalysis:
    """Cohort comparison analysis"""
    cohort_size: int
    cohort_mean_score: float
    cohort_std_dev: float
    candidate_z_score: float
    cohort_percentile: float
    performance_vs_cohort: str

class CaregiverRankingEngine:
    """Real-time ranking engine for caregiver candidates"""
    
    def __init__(self, db_connection_string: str, redis_connection_string: str):
        self.db_connection_string = db_connection_string
        self.redis_connection_string = redis_connection_string
        self.redis_client = None
        
        # Tier thresholds
        self.tier_thresholds = {
            'A+': {'score': 90, 'percentile': 95},
            'A': {'score': 85, 'percentile': 85},
            'A-': {'score': 80, 'percentile': 75},
            'B+': {'score': 75, 'percentile': 60},
            'B': {'score': 70, 'percentile': 40},
            'B-': {'score': 65, 'percentile': 25}
        }
        
        logger.info("CaregiverRankingEngine initialized")
    
    async def initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_connection_string,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")
            raise
    
    async def update_candidate_ranking(self, evaluation: InterviewEvaluation):
        """Update rankings after new interview completion"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Insert or update candidate ranking
            await conn.execute("""
                INSERT INTO candidate_rankings (
                    candidate_id, experience_avg, motivation_score, punctuality_avg,
                    empathy_avg, communication_score, total_weighted_score,
                    confidence_level
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (candidate_id) DO UPDATE SET
                    experience_avg = EXCLUDED.experience_avg,
                    motivation_score = EXCLUDED.motivation_score,
                    punctuality_avg = EXCLUDED.punctuality_avg,
                    empathy_avg = EXCLUDED.empathy_avg,
                    communication_score = EXCLUDED.communication_score,
                    total_weighted_score = EXCLUDED.total_weighted_score,
                    confidence_level = EXCLUDED.confidence_level,
                    last_updated = NOW()
            """, 
            evaluation.candidate_id, evaluation.experience_avg, evaluation.motivation_score,
            evaluation.punctuality_avg, evaluation.empathy_avg, evaluation.communication_score,
            evaluation.total_weighted_score, evaluation.confidence_level)
            
            # Recalculate all rankings
            await self._recalculate_all_rankings(conn)
            
            # Update Redis cache
            await self._update_redis_cache()
            
            await conn.close()
            logger.info(f"Updated ranking for candidate {evaluation.candidate_id}")
            
        except Exception as e:
            logger.error(f"Error updating candidate ranking: {e}")
            raise
    
    async def _recalculate_all_rankings(self, conn: asyncpg.Connection):
        """Recalculate ranks and percentiles for all candidates"""
        try:
            # Get all completed candidates ordered by score
            candidates = await conn.fetch("""
                SELECT cr.candidate_id, cr.total_weighted_score
                FROM candidate_rankings cr
                JOIN interview_sessions is ON cr.candidate_id = is.candidate_id
                WHERE is.session_status = 'completed'
                ORDER BY cr.total_weighted_score DESC
            """)
            
            total_candidates = len(candidates)
            
            # Update ranks, percentiles, and tiers
            for i, candidate in enumerate(candidates):
                rank = i + 1
                percentile = ((total_candidates - rank) / total_candidates) * 100 if total_candidates > 0 else 0
                tier = self._calculate_tier(candidate['total_weighted_score'], percentile)
                
                await conn.execute("""
                    UPDATE candidate_rankings 
                    SET overall_rank = $1, percentile_rank = $2, tier = $3, last_updated = NOW()
                    WHERE candidate_id = $4
                """, rank, percentile, tier, candidate['candidate_id'])
            
            logger.info(f"Recalculated rankings for {total_candidates} candidates")
            
        except Exception as e:
            logger.error(f"Error recalculating rankings: {e}")
            raise
    
    def _calculate_tier(self, score: float, percentile: float) -> str:
        """Calculate tier based on score and percentile"""
        for tier, thresholds in self.tier_thresholds.items():
            if score >= thresholds['score'] and percentile >= thresholds['percentile']:
                return tier
        return 'C'  # Default tier
    
    async def _update_redis_cache(self):
        """Update Redis cache with current rankings"""
        try:
            if not self.redis_client:
                await self.initialize_redis()
            
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Get top candidates for leaderboard
            top_candidates = await conn.fetch("""
                SELECT 
                    cr.overall_rank,
                    c.first_name || ' ' || c.last_name as name,
                    cr.total_weighted_score,
                    cr.tier,
                    cr.percentile_rank,
                    cr.hiring_probability,
                    cr.expected_performance,
                    is.completed_at as interview_date,
                    cr.candidate_id
                FROM candidate_rankings cr
                JOIN candidates c ON cr.candidate_id = c.id
                JOIN interview_sessions is ON c.id = is.candidate_id
                WHERE is.session_status = 'completed'
                ORDER BY cr.overall_rank
                LIMIT 100
            """)
            
            # Cache leaderboard
            leaderboard_data = [
                {
                    'rank': row['overall_rank'],
                    'candidate_id': row['candidate_id'],
                    'name': row['name'],
                    'score': float(row['total_weighted_score']),
                    'tier': row['tier'],
                    'percentile': float(row['percentile_rank']),
                    'hiring_probability': float(row['hiring_probability'] or 0),
                    'expected_performance': float(row['expected_performance'] or 0),
                    'interview_date': row['interview_date'].isoformat() if row['interview_date'] else None
                }
                for row in top_candidates
            ]
            
            await self.redis_client.setex(
                "live_leaderboard", 
                300,  # 5 minutes expiration
                json.dumps(leaderboard_data)
            )
            
            # Cache individual candidate rankings in sorted set
            for candidate in top_candidates:
                await self.redis_client.zadd(
                    "candidate_scores",
                    {candidate['candidate_id']: candidate['total_weighted_score']}
                )
            
            await conn.close()
            logger.info("Redis cache updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating Redis cache: {e}")
    
    async def get_live_leaderboard(self, limit: int = 50) -> List[CandidateRanking]:
        """Get current top candidates from cache or database"""
        try:
            # Try Redis cache first
            if self.redis_client:
                cached_data = await self.redis_client.get("live_leaderboard")
                if cached_data:
                    leaderboard_data = json.loads(cached_data)
                    return [
                        CandidateRanking(
                            candidate_id=item['candidate_id'],
                            candidate_name=item['name'],
                            overall_rank=item['rank'],
                            percentile_rank=item['percentile'],
                            tier=item['tier'],
                            total_weighted_score=item['score'],
                            dimension_scores={},  # Would need separate query for full details
                            hiring_probability=item['hiring_probability'],
                            expected_performance=item['expected_performance'],
                            risk_factors=[],  # Would need separate query
                            confidence_level='medium',  # Default
                            interview_date=datetime.fromisoformat(item['interview_date']) if item['interview_date'] else None
                        )
                        for item in leaderboard_data[:limit]
                    ]
            
            # Fallback to database
            return await self._get_leaderboard_from_database(limit)
            
        except Exception as e:
            logger.error(f"Error getting live leaderboard: {e}")
            return []
    
    async def _get_leaderboard_from_database(self, limit: int) -> List[CandidateRanking]:
        """Get leaderboard directly from database"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            rankings = await conn.fetch("""
                SELECT 
                    cr.candidate_id,
                    c.first_name || ' ' || c.last_name as name,
                    cr.overall_rank,
                    cr.percentile_rank,
                    cr.tier,
                    cr.total_weighted_score,
                    cr.experience_avg,
                    cr.motivation_score,
                    cr.punctuality_avg,
                    cr.empathy_avg,
                    cr.communication_score,
                    cr.hiring_probability,
                    cr.expected_performance,
                    cr.risk_factors,
                    cr.confidence_level,
                    is.completed_at as interview_date
                FROM candidate_rankings cr
                JOIN candidates c ON cr.candidate_id = c.id
                JOIN interview_sessions is ON c.id = is.candidate_id
                WHERE is.session_status = 'completed'
                ORDER BY cr.overall_rank
                LIMIT $1
            """, limit)
            
            await conn.close()
            
            return [
                CandidateRanking(
                    candidate_id=row['candidate_id'],
                    candidate_name=row['name'],
                    overall_rank=row['overall_rank'],
                    percentile_rank=float(row['percentile_rank']),
                    tier=row['tier'],
                    total_weighted_score=float(row['total_weighted_score']),
                    dimension_scores={
                        'experience': float(row['experience_avg']),
                        'motivation': float(row['motivation_score']),
                        'punctuality': float(row['punctuality_avg']),
                        'empathy': float(row['empathy_avg']),
                        'communication': float(row['communication_score'])
                    },
                    hiring_probability=float(row['hiring_probability'] or 0),
                    expected_performance=float(row['expected_performance'] or 0),
                    risk_factors=row['risk_factors'] or [],
                    confidence_level=row['confidence_level'],
                    interview_date=row['interview_date']
                )
                for row in rankings
            ]
            
        except Exception as e:
            logger.error(f"Error getting leaderboard from database: {e}")
            return []
    
    async def get_candidate_details(self, candidate_id: str) -> Optional[Dict]:
        """Get detailed information for a specific candidate"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Get candidate ranking and details
            candidate_data = await conn.fetchrow("""
                SELECT 
                    c.first_name, c.last_name, c.email, c.phone,
                    c.caregiving_experience, c.weekly_hours,
                    cr.overall_rank, cr.percentile_rank, cr.tier,
                    cr.total_weighted_score, cr.experience_avg, cr.motivation_score,
                    cr.punctuality_avg, cr.empathy_avg, cr.communication_score,
                    cr.hiring_probability, cr.expected_performance, cr.risk_factors,
                    cr.confidence_level, is.completed_at, is.audio_filename
                FROM candidates c
                JOIN candidate_rankings cr ON c.id = cr.candidate_id
                JOIN interview_sessions is ON c.id = is.candidate_id
                WHERE c.id = $1 AND is.session_status = 'completed'
            """, candidate_id)
            
            if not candidate_data:
                return None
            
            # Get question responses
            question_responses = await conn.fetch("""
                SELECT question_id, question_text, candidate_answer,
                       final_question_score, rag_best_match_score, rag_match_quality,
                       empathy_bonus, patient_story_bonus
                FROM question_responses
                WHERE session_id = (
                    SELECT id FROM interview_sessions 
                    WHERE candidate_id = $1 AND session_status = 'completed'
                )
                ORDER BY question_id
            """, candidate_id)
            
            await conn.close()
            
            return {
                'candidate_info': {
                    'id': candidate_id,
                    'name': f"{candidate_data['first_name']} {candidate_data['last_name']}",
                    'email': candidate_data['email'],
                    'phone': candidate_data['phone'],
                    'caregiving_experience': candidate_data['caregiving_experience'],
                    'weekly_hours': candidate_data['weekly_hours']
                },
                'ranking_info': {
                    'overall_rank': candidate_data['overall_rank'],
                    'percentile_rank': float(candidate_data['percentile_rank']),
                    'tier': candidate_data['tier'],
                    'total_score': float(candidate_data['total_weighted_score']),
                    'hiring_probability': float(candidate_data['hiring_probability'] or 0),
                    'expected_performance': float(candidate_data['expected_performance'] or 0),
                    'confidence_level': candidate_data['confidence_level']
                },
                'dimension_scores': {
                    'experience': float(candidate_data['experience_avg']),
                    'motivation': float(candidate_data['motivation_score']),
                    'punctuality': float(candidate_data['punctuality_avg']),
                    'empathy': float(candidate_data['empathy_avg']),
                    'communication': float(candidate_data['communication_score'])
                },
                'question_details': [
                    {
                        'question_id': row['question_id'],
                        'question_text': row['question_text'],
                        'candidate_answer': row['candidate_answer'],
                        'final_score': float(row['final_question_score']),
                        'rag_similarity': float(row['rag_best_match_score']),
                        'rag_quality': row['rag_match_quality'],
                        'empathy_bonus': float(row['empathy_bonus']),
                        'patient_story_bonus': float(row['patient_story_bonus'])
                    }
                    for row in question_responses
                ],
                'risk_factors': candidate_data['risk_factors'] or [],
                'interview_metadata': {
                    'completed_at': candidate_data['completed_at'].isoformat() if candidate_data['completed_at'] else None,
                    'audio_filename': candidate_data['audio_filename']
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting candidate details: {e}")
            return None
    
    async def get_cohort_analysis(self, candidate_id: str) -> Optional[CohortAnalysis]:
        """Perform cohort analysis for a candidate"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Get candidate's profile for cohort matching
            candidate_profile = await conn.fetchrow("""
                SELECT c.caregiving_experience, c.weekly_hours, cr.total_weighted_score
                FROM candidates c
                JOIN candidate_rankings cr ON c.id = cr.candidate_id
                WHERE c.id = $1
            """, candidate_id)
            
            if not candidate_profile:
                return None
            
            # Find similar candidates (cohort)
            cohort_candidates = await conn.fetch("""
                SELECT cr.total_weighted_score
                FROM candidate_rankings cr
                JOIN candidates c ON cr.candidate_id = c.id
                JOIN interview_sessions is ON c.id = is.candidate_id
                WHERE is.session_status = 'completed'
                  AND c.caregiving_experience = $1
                  AND ABS(c.weekly_hours - $2) <= 10  -- Similar availability
                  AND cr.candidate_id != $3  -- Exclude current candidate
            """, 
            candidate_profile['caregiving_experience'],
            candidate_profile['weekly_hours'],
            candidate_id)
            
            if len(cohort_candidates) < 5:
                # Expand criteria if cohort too small
                cohort_candidates = await conn.fetch("""
                    SELECT cr.total_weighted_score
                    FROM candidate_rankings cr
                    JOIN candidates c ON cr.candidate_id = c.id
                    JOIN interview_sessions is ON c.id = is.candidate_id
                    WHERE is.session_status = 'completed'
                      AND c.caregiving_experience = $1
                      AND cr.candidate_id != $2
                """, candidate_profile['caregiving_experience'], candidate_id)
            
            await conn.close()
            
            if not cohort_candidates:
                return None
            
            # Calculate cohort statistics
            cohort_scores = [float(row['total_weighted_score']) for row in cohort_candidates]
            cohort_mean = np.mean(cohort_scores)
            cohort_std = np.std(cohort_scores)
            
            # Calculate candidate's position in cohort
            candidate_score = float(candidate_profile['total_weighted_score'])
            z_score = (candidate_score - cohort_mean) / cohort_std if cohort_std > 0 else 0
            
            # Calculate cohort percentile
            better_count = sum(1 for score in cohort_scores if score < candidate_score)
            cohort_percentile = (better_count / len(cohort_scores)) * 100
            
            # Interpret performance
            if z_score >= 1.5:
                performance = "exceptional"
            elif z_score >= 0.5:
                performance = "above_average"
            elif z_score >= -0.5:
                performance = "average"
            else:
                performance = "below_average"
            
            return CohortAnalysis(
                cohort_size=len(cohort_candidates),
                cohort_mean_score=cohort_mean,
                cohort_std_dev=cohort_std,
                candidate_z_score=z_score,
                cohort_percentile=cohort_percentile,
                performance_vs_cohort=performance
            )
            
        except Exception as e:
            logger.error(f"Error performing cohort analysis: {e}")
            return None
    
    async def get_ranking_analytics(self, days: int = 30) -> Dict:
        """Get comprehensive ranking analytics"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Get summary statistics
            summary = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_candidates,
                    AVG(cr.total_weighted_score) as avg_score,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cr.total_weighted_score) as median_score,
                    STDDEV(cr.total_weighted_score) as score_std_dev,
                    MIN(cr.total_weighted_score) as min_score,
                    MAX(cr.total_weighted_score) as max_score
                FROM candidate_rankings cr
                JOIN interview_sessions is ON cr.candidate_id = is.candidate_id
                WHERE is.session_status = 'completed'
                  AND is.completed_at >= NOW() - INTERVAL '%s days'
            """, days)
            
            # Get tier distribution
            tier_distribution = await conn.fetch("""
                SELECT tier, COUNT(*) as count
                FROM candidate_rankings cr
                JOIN interview_sessions is ON cr.candidate_id = is.candidate_id
                WHERE is.session_status = 'completed'
                  AND is.completed_at >= NOW() - INTERVAL '%s days'
                GROUP BY tier
                ORDER BY tier
            """, days)
            
            # Get recommendation distribution
            recommendation_distribution = await conn.fetch("""
                SELECT recommendation, COUNT(*) as count
                FROM interview_sessions
                WHERE session_status = 'completed'
                  AND completed_at >= NOW() - INTERVAL '%s days'
                GROUP BY recommendation
            """, days)
            
            await conn.close()
            
            return {
                'summary_statistics': {
                    'total_candidates': summary['total_candidates'],
                    'average_score': float(summary['avg_score'] or 0),
                    'median_score': float(summary['median_score'] or 0),
                    'score_std_dev': float(summary['score_std_dev'] or 0),
                    'score_range': {
                        'min': float(summary['min_score'] or 0),
                        'max': float(summary['max_score'] or 0)
                    }
                },
                'tier_distribution': {
                    row['tier']: row['count'] for row in tier_distribution
                },
                'recommendation_distribution': {
                    row['recommendation']: row['count'] for row in recommendation_distribution
                },
                'timeframe_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting ranking analytics: {e}")
            return {}
    
    async def get_candidates_by_tier(self, tier: str, limit: int = 20) -> List[CandidateRanking]:
        """Get candidates filtered by tier"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            candidates = await conn.fetch("""
                SELECT 
                    cr.candidate_id,
                    c.first_name || ' ' || c.last_name as name,
                    cr.overall_rank,
                    cr.percentile_rank,
                    cr.tier,
                    cr.total_weighted_score,
                    cr.experience_avg,
                    cr.motivation_score,
                    cr.punctuality_avg,
                    cr.empathy_avg,
                    cr.communication_score,
                    cr.hiring_probability,
                    cr.expected_performance,
                    cr.risk_factors,
                    cr.confidence_level,
                    is.completed_at as interview_date
                FROM candidate_rankings cr
                JOIN candidates c ON cr.candidate_id = c.id
                JOIN interview_sessions is ON c.id = is.candidate_id
                WHERE cr.tier = $1 AND is.session_status = 'completed'
                ORDER BY cr.overall_rank
                LIMIT $2
            """, tier, limit)
            
            await conn.close()
            
            return [
                CandidateRanking(
                    candidate_id=row['candidate_id'],
                    candidate_name=row['name'],
                    overall_rank=row['overall_rank'],
                    percentile_rank=float(row['percentile_rank']),
                    tier=row['tier'],
                    total_weighted_score=float(row['total_weighted_score']),
                    dimension_scores={
                        'experience': float(row['experience_avg']),
                        'motivation': float(row['motivation_score']),
                        'punctuality': float(row['punctuality_avg']),
                        'empathy': float(row['empathy_avg']),
                        'communication': float(row['communication_score'])
                    },
                    hiring_probability=float(row['hiring_probability'] or 0),
                    expected_performance=float(row['expected_performance'] or 0),
                    risk_factors=row['risk_factors'] or [],
                    confidence_level=row['confidence_level'],
                    interview_date=row['interview_date']
                )
                for row in candidates
            ]
            
        except Exception as e:
            logger.error(f"Error getting candidates by tier: {e}")
            return []

# Example usage
async def main():
    """Example usage of the ranking engine"""
    from .rag_system import CaregiverRAGSystem
    
    # Initialize components
    db_connection = "postgresql://interview_admin:secure_password@localhost:5432/interview_bot"
    redis_connection = "redis://localhost:6379/0"
    
    rag_system = CaregiverRAGSystem(db_connection)
    await rag_system.initialize_expected_answers()
    
    ranking_engine = CaregiverRankingEngine(db_connection, redis_connection)
    await ranking_engine.initialize_redis()
    
    # Get live leaderboard
    leaderboard = await ranking_engine.get_live_leaderboard(10)
    
    print("Top 10 Candidates:")
    for candidate in leaderboard:
        print(f"#{candidate.overall_rank}: {candidate.candidate_name} - "
              f"Score: {candidate.total_weighted_score:.1f}/100, "
              f"Tier: {candidate.tier}, "
              f"Hiring Probability: {candidate.hiring_probability:.0%}")

if __name__ == "__main__":
    asyncio.run(main())
