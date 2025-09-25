"""
RAG System for Semantic Answer Evaluation
Integrates with vector database for intelligent caregiver interview scoring
"""

import os
import json
import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from elasticsearch import AsyncElasticsearch
import asyncpg
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RAGMatch:
    """Represents a RAG similarity match result"""
    answer_id: str
    similarity_score: float
    quality_level: str
    score_range_min: int
    score_range_max: int
    empathy_indicators: List[str]
    experience_indicators: List[str]
    behavioral_patterns: List[str]
    answer_text: str

@dataclass
class RAGEvaluationResult:
    """Complete RAG evaluation result for a candidate answer"""
    semantic_similarity_score: float
    best_match: RAGMatch
    quality_mapping_score: float
    empathy_bonus: float
    patient_story_bonus: float
    care_experience_bonus: float
    dignity_mention_bonus: float
    final_score: float
    confidence_level: str

class CaregiverRAGSystem:
    """RAG system specifically designed for caregiver interview evaluation"""
    
    def __init__(self, db_connection_string: str, elasticsearch_url: str = "http://localhost:9200"):
        self.db_connection_string = db_connection_string
        self.elasticsearch_url = elasticsearch_url
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize Elasticsearch client
        self.es_client = AsyncElasticsearch([elasticsearch_url])
        
        # Index name for caregiver answers
        self.index_name = "caregiver_answers"
        
        # Caregiver-specific keywords and patterns
        self.empathy_keywords = [
            "patience", "understanding", "compassion", "dignity", "respect",
            "gentle", "kind", "caring", "empathy", "comfort", "support",
            "listen", "emotional", "feelings", "person-centered", "individual"
        ]
        
        self.patient_story_keywords = [
            "grandmother", "grandfather", "mother", "father", "patient", "resident",
            "client", "years", "months", "experience", "cared for", "took care",
            "helped", "assisted", "worked with"
        ]
        
        self.care_experience_keywords = [
            "CNA", "certified", "nursing", "healthcare", "medical", "hospital",
            "facility", "assisted living", "home care", "dementia", "alzheimer",
            "medication", "mobility", "transfer", "personal care"
        ]
        
        self.dignity_keywords = [
            "dignity", "respect", "choice", "independence", "privacy",
            "person first", "individual", "human", "worth", "value"
        ]
        
        logger.info("CaregiverRAGSystem initialized successfully")
    
    async def initialize_elasticsearch_index(self):
        """Initialize Elasticsearch index with proper mapping"""
        try:
            # Create index with vector mapping
            index_mapping = {
                "mappings": {
                    "properties": {
                        "question_id": {"type": "keyword"},
                        "answer_text": {"type": "text"},
                        "quality_level": {"type": "keyword"},
                        "score_range_min": {"type": "integer"},
                        "score_range_max": {"type": "integer"},
                        "empathy_indicators": {"type": "keyword"},
                        "experience_indicators": {"type": "keyword"},
                        "behavioral_patterns": {"type": "keyword"},
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 384,  # Sentence transformer dimension
                            "index": True,
                            "similarity": "cosine"
                        },
                        "created_at": {"type": "date"}
                    }
                }
            }
            
            # Check if index exists
            if await self.es_client.indices.exists(index=self.index_name):
                logger.info(f"Elasticsearch index '{self.index_name}' already exists")
            else:
                await self.es_client.indices.create(index=self.index_name, body=index_mapping)
                logger.info(f"Created Elasticsearch index '{self.index_name}'")
                
        except Exception as e:
            logger.error(f"Error initializing Elasticsearch index: {e}")
            raise
    
    async def initialize_expected_answers(self):
        """Load expected answers from database into vector database"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Get expected answers from database
            expected_answers = await conn.fetch("""
                SELECT id, question_id, answer_text, quality_level,
                       score_range_min, score_range_max,
                       empathy_indicators, experience_indicators, behavioral_patterns
                FROM expected_answers
            """)
            
            if not expected_answers:
                logger.warning("No expected answers found in database")
                await conn.close()
                return
            
            # Initialize Elasticsearch index first
            await self.initialize_elasticsearch_index()
            
            # Generate embeddings and store in Elasticsearch
            for answer in expected_answers:
                # Generate embedding
                embedding = self.embedding_model.encode(answer['answer_text']).tolist()
                
                # Prepare document for Elasticsearch
                doc = {
                    "question_id": answer['question_id'],
                    "answer_text": answer['answer_text'],
                    "quality_level": answer['quality_level'],
                    "score_range_min": answer['score_range_min'],
                    "score_range_max": answer['score_range_max'],
                    "empathy_indicators": answer['empathy_indicators'],
                    "experience_indicators": answer['experience_indicators'],
                    "behavioral_patterns": answer['behavioral_patterns'],
                    "embedding": embedding,
                    "created_at": datetime.now().isoformat()
                }
                
                # Index document in Elasticsearch
                await self.es_client.index(
                    index=self.index_name,
                    id=answer['id'],
                    body=doc
                )
            
            # Refresh index to make documents searchable
            await self.es_client.indices.refresh(index=self.index_name)
            
            await conn.close()
            logger.info(f"Loaded {len(expected_answers)} expected answers into vector database")
            
        except Exception as e:
            logger.error(f"Error initializing expected answers: {e}")
            raise
    
    async def evaluate_answer(self, question_id: str, candidate_answer: str) -> RAGEvaluationResult:
        """
        Evaluate a candidate answer using RAG system
        
        Args:
            question_id: The question identifier (Q1, Q2, etc.)
            candidate_answer: The candidate's response text
            
        Returns:
            RAGEvaluationResult with complete evaluation
        """
        try:
            # Generate embedding for candidate answer
            candidate_embedding = self.embedding_model.encode(candidate_answer).tolist()
            
            # Search for similar answers using Elasticsearch vector search
            search_query = {
                "size": 5,
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"question_id": question_id}}
                        ]
                    }
                },
                "knn": {
                    "field": "embedding",
                    "query_vector": candidate_embedding,
                    "k": 5,
                    "num_candidates": 50,
                    "filter": {
                        "term": {"question_id": question_id}
                    }
                }
            }
            
            results = await self.es_client.search(index=self.index_name, body=search_query)
            
            if not results['hits']['hits']:
                logger.warning(f"No expected answers found for question {question_id}")
                return self._create_default_result()
            
            # Get best match (highest score)
            best_hit = results['hits']['hits'][0]
            best_similarity = best_hit['_score'] / 100  # Normalize to 0-1 range
            best_source = best_hit['_source']
            
            # Create RAGMatch object
            best_match = RAGMatch(
                answer_id=best_hit['_id'],
                similarity_score=best_similarity,
                quality_level=best_source['quality_level'],
                score_range_min=best_source['score_range_min'],
                score_range_max=best_source['score_range_max'],
                empathy_indicators=best_source['empathy_indicators'],
                experience_indicators=best_source['experience_indicators'],
                behavioral_patterns=best_source['behavioral_patterns'],
                answer_text=best_source['answer_text']
            )
            
            # Calculate semantic similarity score (0-100)
            semantic_score = best_similarity * 100
            
            # Map to quality-based score
            quality_score = self._map_similarity_to_score(best_similarity, best_match)
            
            # Calculate caregiver-specific bonuses
            empathy_bonus = self._calculate_empathy_bonus(candidate_answer)
            patient_story_bonus = self._calculate_patient_story_bonus(candidate_answer)
            care_experience_bonus = self._calculate_care_experience_bonus(candidate_answer)
            dignity_mention_bonus = self._calculate_dignity_mention_bonus(candidate_answer)
            
            # Calculate final score with bonuses
            final_score = min(
                quality_score * empathy_bonus * patient_story_bonus * 
                care_experience_bonus * dignity_mention_bonus,
                100.0
            )
            
            # Determine confidence level
            confidence_level = self._calculate_confidence_level(best_similarity, len(results['ids'][0]))
            
            return RAGEvaluationResult(
                semantic_similarity_score=semantic_score,
                best_match=best_match,
                quality_mapping_score=quality_score,
                empathy_bonus=empathy_bonus,
                patient_story_bonus=patient_story_bonus,
                care_experience_bonus=care_experience_bonus,
                dignity_mention_bonus=dignity_mention_bonus,
                final_score=final_score,
                confidence_level=confidence_level
            )
            
        except Exception as e:
            logger.error(f"Error evaluating answer: {e}")
            return self._create_default_result()
    
    def _map_similarity_to_score(self, similarity: float, match: RAGMatch) -> float:
        """Map similarity score to quality-based score range"""
        if match.quality_level == 'excellent' and similarity > 0.85:
            # Map 0.85-1.0 similarity to 90-100 score range
            return 90 + (similarity - 0.85) * 66.67  # (100-90)/(1.0-0.85)
        elif match.quality_level == 'good' and similarity > 0.75:
            # Map 0.75-1.0 similarity to 75-90 score range
            return 75 + (similarity - 0.75) * 60  # (90-75)/(1.0-0.75)
        elif match.quality_level == 'fair' and similarity > 0.65:
            # Map 0.65-1.0 similarity to 60-75 score range
            return 60 + (similarity - 0.65) * 42.86  # (75-60)/(1.0-0.65)
        else:
            # Linear mapping for lower similarities
            return similarity * 100
    
    def _calculate_empathy_bonus(self, answer: str) -> float:
        """Calculate empathy bonus based on compassionate language"""
        answer_lower = answer.lower()
        empathy_count = sum(1 for keyword in self.empathy_keywords if keyword in answer_lower)
        
        if empathy_count >= 3:
            return 1.12  # 12% bonus for strong empathy
        elif empathy_count >= 2:
            return 1.08  # 8% bonus for moderate empathy
        elif empathy_count >= 1:
            return 1.05  # 5% bonus for some empathy
        else:
            return 1.0   # No bonus
    
    def _calculate_patient_story_bonus(self, answer: str) -> float:
        """Calculate bonus for sharing patient care stories"""
        answer_lower = answer.lower()
        story_count = sum(1 for keyword in self.patient_story_keywords if keyword in answer_lower)
        
        # Look for story patterns (past tense, personal experience)
        story_patterns = ["i cared", "i helped", "i worked", "i took care", "when i", "i learned"]
        pattern_count = sum(1 for pattern in story_patterns if pattern in answer_lower)
        
        total_indicators = story_count + pattern_count
        
        if total_indicators >= 4:
            return 1.08  # 8% bonus for detailed patient stories
        elif total_indicators >= 2:
            return 1.05  # 5% bonus for some patient experience
        else:
            return 1.0   # No bonus
    
    def _calculate_care_experience_bonus(self, answer: str) -> float:
        """Calculate bonus for demonstrating care experience"""
        answer_lower = answer.lower()
        experience_count = sum(1 for keyword in self.care_experience_keywords if keyword in answer_lower)
        
        if experience_count >= 3:
            return 1.05  # 5% bonus for professional experience
        else:
            return 1.0   # No bonus
    
    def _calculate_dignity_mention_bonus(self, answer: str) -> float:
        """Calculate bonus for mentioning dignity and respect"""
        answer_lower = answer.lower()
        dignity_count = sum(1 for keyword in self.dignity_keywords if keyword in answer_lower)
        
        if dignity_count >= 1:
            return 1.05  # 5% bonus for dignity-focused language
        else:
            return 1.0   # No bonus
    
    def _calculate_confidence_level(self, similarity: float, num_matches: int) -> str:
        """Calculate confidence level based on similarity and available matches"""
        if similarity > 0.85 and num_matches >= 3:
            return "high"
        elif similarity > 0.70 and num_matches >= 2:
            return "medium"
        else:
            return "low"
    
    def _create_default_result(self) -> RAGEvaluationResult:
        """Create default result when RAG evaluation fails"""
        default_match = RAGMatch(
            answer_id="default",
            similarity_score=0.5,
            quality_level="fair",
            score_range_min=50,
            score_range_max=70,
            empathy_indicators=[],
            experience_indicators=[],
            behavioral_patterns=[],
            answer_text=""
        )
        
        return RAGEvaluationResult(
            semantic_similarity_score=50.0,
            best_match=default_match,
            quality_mapping_score=50.0,
            empathy_bonus=1.0,
            patient_story_bonus=1.0,
            care_experience_bonus=1.0,
            dignity_mention_bonus=1.0,
            final_score=50.0,
            confidence_level="low"
        )
    
    async def add_expected_answer(self, question_id: str, answer_text: str, 
                                quality_level: str, empathy_indicators: List[str],
                                experience_indicators: List[str], 
                                behavioral_patterns: List[str]) -> str:
        """Add a new expected answer to both database and vector store"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Generate unique ID
            answer_id = f"{question_id}_{quality_level}_{hash(answer_text) % 10000:04d}"
            
            # Determine score range based on quality
            score_ranges = {
                'excellent': (90, 100),
                'good': (75, 90),
                'fair': (60, 75),
                'poor': (0, 60)
            }
            score_min, score_max = score_ranges.get(quality_level, (50, 70))
            
            # Insert into database
            await conn.execute("""
                INSERT INTO expected_answers 
                (id, question_id, answer_text, quality_level, score_range_min, score_range_max,
                 empathy_indicators, experience_indicators, behavioral_patterns, embedding_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, answer_id, question_id, answer_text, quality_level, score_min, score_max,
            json.dumps(empathy_indicators), json.dumps(experience_indicators),
            json.dumps(behavioral_patterns), f"{answer_id}_embedding")
            
            # Generate embedding and add to Elasticsearch
            embedding = self.embedding_model.encode(answer_text).tolist()
            
            doc = {
                "question_id": question_id,
                "answer_text": answer_text,
                "quality_level": quality_level,
                "score_range_min": score_min,
                "score_range_max": score_max,
                "empathy_indicators": empathy_indicators,
                "experience_indicators": experience_indicators,
                "behavioral_patterns": behavioral_patterns,
                "embedding": embedding,
                "created_at": datetime.now().isoformat()
            }
            
            await self.es_client.index(
                index=self.index_name,
                id=answer_id,
                body=doc
            )
            
            await conn.close()
            logger.info(f"Added expected answer {answer_id} for question {question_id}")
            return answer_id
            
        except Exception as e:
            logger.error(f"Error adding expected answer: {e}")
            raise
    
    async def get_rag_analytics(self, days: int = 30) -> Dict:
        """Get analytics on RAG system performance"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            analytics = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_evaluations,
                    AVG(rag_best_match_score) as avg_similarity,
                    AVG(final_question_score) as avg_final_score,
                    COUNT(CASE WHEN rag_match_quality = 'excellent' THEN 1 END) as excellent_matches,
                    COUNT(CASE WHEN rag_match_quality = 'good' THEN 1 END) as good_matches,
                    COUNT(CASE WHEN rag_match_quality = 'fair' THEN 1 END) as fair_matches,
                    AVG(empathy_bonus) as avg_empathy_bonus,
                    COUNT(CASE WHEN empathy_bonus > 1.0 THEN 1 END) as empathy_bonus_count
                FROM question_responses qr
                JOIN interview_sessions is ON qr.session_id = is.id
                WHERE is.session_status = 'completed'
                  AND qr.created_at >= NOW() - INTERVAL '%s days'
            """, days)
            
            await conn.close()
            
            return {
                'total_evaluations': analytics['total_evaluations'],
                'avg_similarity': float(analytics['avg_similarity'] or 0),
                'avg_final_score': float(analytics['avg_final_score'] or 0),
                'quality_distribution': {
                    'excellent': analytics['excellent_matches'],
                    'good': analytics['good_matches'],
                    'fair': analytics['fair_matches']
                },
                'empathy_metrics': {
                    'avg_bonus': float(analytics['avg_empathy_bonus'] or 1.0),
                    'bonus_frequency': analytics['empathy_bonus_count']
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting RAG analytics: {e}")
            return {}

# Example usage and testing
async def main():
    """Example usage of the RAG system"""
    # Initialize RAG system
    db_connection = "postgresql://interview_admin:secure_password@localhost:5432/interview_bot"
    rag_system = CaregiverRAGSystem(db_connection)
    
    # Initialize expected answers
    await rag_system.initialize_expected_answers()
    
    # Test evaluation
    test_answer = """I took care of my grandmother who had Alzheimer's for about 18 months. 
    It was really challenging because she would get confused and sometimes not recognize me. 
    But I learned to be patient and always speak to her with respect. I found that playing 
    her favorite music helped calm her down when she got agitated. The most important thing 
    I learned is that even though her memory was fading, she was still a person who deserved 
    dignity and love."""
    
    result = await rag_system.evaluate_answer("Q7", test_answer)
    
    print(f"Semantic Similarity: {result.semantic_similarity_score:.1f}/100")
    print(f"Quality Mapping Score: {result.quality_mapping_score:.1f}/100")
    print(f"Empathy Bonus: {result.empathy_bonus:.2f}x")
    print(f"Patient Story Bonus: {result.patient_story_bonus:.2f}x")
    print(f"Final Score: {result.final_score:.1f}/100")
    print(f"Confidence: {result.confidence_level}")
    print(f"Best Match Quality: {result.best_match.quality_level}")

if __name__ == "__main__":
    asyncio.run(main())
