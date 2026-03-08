"""
Setup Script for Enhanced AI Interviewer Bot
Initializes database, populates expected answers, and sets up the enhanced system
"""

import os
import sys
import asyncio
import asyncpg
import json
from datetime import datetime

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.rag_system import CaregiverRAGSystem
from app.enhanced_scoring_engine import CaregiverScoringEngine
from app.ranking_engine import CaregiverRankingEngine
from app.ml_predictions import CaregiverMLPredictor

class EnhancedSystemSetup:
    """Setup and initialization for the enhanced interview system"""
    
    def __init__(self):
        self.db_connection = os.getenv(
            'DATABASE_URL', 
            'postgresql://interview_admin:secure_password@localhost:5432/interview_bot'
        )
        self.redis_connection = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.elasticsearch_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
        
    async def setup_database(self):
        """Set up database schema and initial data"""
        print("🗄️  Setting up database schema...")
        
        try:
            # Read schema file
            schema_file = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            # Connect and execute schema
            conn = await asyncpg.connect(self.db_connection)
            await conn.execute(schema_sql)
            await conn.close()
            
            print("✅ Database schema created successfully")
            
        except Exception as e:
            print(f"❌ Error setting up database: {e}")
            raise
    
    async def populate_expected_answers(self):
        """Populate the database with expected answers for RAG system"""
        print("📚 Populating expected answers for RAG system...")
        
        try:
            conn = await asyncpg.connect(self.db_connection)
            
            # Expected answers for each question
            expected_answers = [
                # Q1: Caregiver Experience
                {
                    'id': 'Q1_excellent_001',
                    'question_id': 'Q1',
                    'answer_text': 'I worked as a certified nursing assistant for 3 years at Sunrise Senior Living. I cared for residents with various conditions including dementia, diabetes, and mobility issues. My daily responsibilities included assisting with personal care, medication reminders, meal assistance, and providing emotional support. I helped with transfers using proper body mechanics and gait belts, and I was trained in infection control protocols. What I found most rewarding was building relationships with residents and seeing how small acts of kindness could brighten their day.',
                    'quality_level': 'excellent',
                    'score_range_min': 90,
                    'score_range_max': 100,
                    'empathy_indicators': ["compassion", "relationships", "kindness", "emotional_support"],
                    'experience_indicators': ["CNA_certification", "3_years", "diverse_conditions", "technical_skills"],
                    'behavioral_patterns': ["specific_duties", "professional_training", "measurable_outcomes"]
                },
                
                # Q2: Ideal Caregiver Traits
                {
                    'id': 'Q2_excellent_001',
                    'question_id': 'Q2',
                    'answer_text': 'For my loved one, I would want a caregiver who is patient, compassionate, and reliable. They should have experience with the specific condition my family member has, whether that\'s dementia, mobility issues, or chronic illness. Communication skills are crucial - they need to listen to my loved one and keep our family informed. I\'d also want someone who respects their dignity and independence, encouraging them to do what they can while providing help where needed. Trust and honesty are essential because we\'re inviting this person into our most vulnerable moments.',
                    'quality_level': 'excellent',
                    'score_range_min': 90,
                    'score_range_max': 100,
                    'empathy_indicators': ["patient", "compassionate", "dignity", "respect", "understanding"],
                    'experience_indicators': ["specific_condition_experience", "communication_skills", "family_involvement"],
                    'behavioral_patterns': ["comprehensive_thinking", "family_perspective", "trust_building"]
                },
                
                # Q7: Senior Care Experience
                {
                    'id': 'Q7_excellent_001',
                    'question_id': 'Q7',
                    'answer_text': 'I cared for my grandmother with dementia for two years after she moved in with us. The most difficult part was watching her confusion and frustration, especially during sundowning episodes. She would sometimes not recognize me or become agitated. I learned to stay calm, use simple words, and redirect her attention to activities she enjoyed like looking at old photos. The most meaningful part was realizing that even though her memory was fading, her emotions and need for connection remained. When I played her favorite music or held her hand, I could see glimpses of the grandmother I knew. It taught me that dignity and respect are crucial in caregiving, and that the person is still there even when the disease progresses.',
                    'quality_level': 'excellent',
                    'score_range_min': 90,
                    'score_range_max': 100,
                    'empathy_indicators': ["patience", "dignity", "emotional_intelligence", "person_centered_care", "understanding"],
                    'experience_indicators': ["2_years_experience", "dementia_care", "behavioral_management", "adaptive_strategies"],
                    'behavioral_patterns': ["situation_personal", "challenges_acknowledged", "actions_compassionate", "learning_demonstrated"]
                },
                
                # Q8: Emotional Support
                {
                    'id': 'Q8_excellent_001',
                    'question_id': 'Q8',
                    'answer_text': 'A colleague was struggling after losing a patient she had cared for over several months. She was questioning whether she was cut out for this work. I sat with her during our break and just listened while she talked about her feelings. I validated that it\'s normal to grieve when we lose someone we\'ve cared for - it shows we\'re human and that we truly care. I shared that the patient had often mentioned how much my colleague\'s kindness meant to her. I offered to help with her workload for a few days while she processed her grief. Later, I connected her with our employee assistance program for additional support.',
                    'quality_level': 'excellent',
                    'score_range_min': 90,
                    'score_range_max': 100,
                    'empathy_indicators': ["listening", "validation", "emotional_support", "understanding", "compassion"],
                    'experience_indicators': ["workplace_support", "grief_understanding", "resource_connection", "professional_boundaries"],
                    'behavioral_patterns': ["active_listening", "emotional_validation", "practical_support", "professional_resources"]
                }
            ]
            
            # Insert expected answers
            for answer in expected_answers:
                await conn.execute("""
                    INSERT INTO expected_answers (
                        id, question_id, answer_text, quality_level, score_range_min, score_range_max,
                        empathy_indicators, experience_indicators, behavioral_patterns, embedding_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (id) DO NOTHING
                """, 
                answer['id'], answer['question_id'], answer['answer_text'], answer['quality_level'],
                answer['score_range_min'], answer['score_range_max'],
                json.dumps(answer['empathy_indicators']), json.dumps(answer['experience_indicators']),
                json.dumps(answer['behavioral_patterns']), f"{answer['id']}_embedding")
            
            await conn.close()
            print(f"✅ Populated {len(expected_answers)} expected answers")
            
        except Exception as e:
            print(f"❌ Error populating expected answers: {e}")
            raise
    
    async def initialize_rag_system(self):
        """Initialize RAG system with vector database"""
        print("🧠 Initializing RAG system...")
        
        try:
            rag_system = CaregiverRAGSystem(self.db_connection, self.elasticsearch_url)
            await rag_system.initialize_expected_answers()
            print("✅ RAG system with Elasticsearch initialized successfully")
            return rag_system
            
        except Exception as e:
            print(f"❌ Error initializing RAG system: {e}")
            raise
    
    async def initialize_ml_models(self):
        """Initialize and train ML models"""
        print("🤖 Initializing ML prediction models...")
        
        try:
            ml_predictor = CaregiverMLPredictor(self.db_connection)
            
            # Train models (will use synthetic data if no historical data)
            performance = await ml_predictor.train_models()
            
            print(f"✅ ML models trained successfully")
            print(f"   - Hiring model accuracy: {performance.accuracy:.3f}")
            print(f"   - Cross-validation score: {performance.cross_val_score:.3f}")
            
            return ml_predictor
            
        except Exception as e:
            print(f"❌ Error initializing ML models: {e}")
            raise
    
    async def test_system_integration(self):
        """Test the complete system integration"""
        print("🧪 Testing system integration...")
        
        try:
            # Initialize all components
            rag_system = CaregiverRAGSystem(self.db_connection)
            await rag_system.initialize_expected_answers()
            
            scoring_engine = CaregiverScoringEngine(self.db_connection, rag_system)
            
            ranking_engine = CaregiverRankingEngine(self.db_connection, self.redis_connection)
            await ranking_engine.initialize_redis()
            
            ml_predictor = CaregiverMLPredictor(self.db_connection)
            await ml_predictor.load_models()
            
            # Test with sample data
            test_answer = "I took care of my elderly neighbor for 6 months when she broke her hip. I helped with daily tasks like cooking, cleaning, and getting to medical appointments. The most challenging part was helping her maintain her independence while ensuring her safety. I learned to be patient and to listen to her concerns about losing her autonomy."
            
            # Test RAG evaluation
            rag_result = await rag_system.evaluate_answer("Q7", test_answer)
            print(f"   - RAG evaluation: {rag_result.final_score:.1f}/100 (Quality: {rag_result.best_match.quality_level})")
            
            # Test ML prediction
            test_features = {
                'experience_avg': 75, 'motivation_score': 80, 'punctuality_avg': 70,
                'empathy_avg': 85, 'communication_score': 78, 'consistency_factor': 1.02,
                'overall_quality_factor': 1.05, 'avg_empathy_bonus': 1.08,
                'avg_patient_story_bonus': 1.05, 'caregiving_experience': False, 'weekly_hours': 25
            }
            
            ml_result = await ml_predictor.predict_hiring_success(test_features)
            print(f"   - ML prediction: {ml_result.hiring_probability:.1%} hiring probability")
            
            print("✅ System integration test completed successfully")
            
        except Exception as e:
            print(f"❌ Error in system integration test: {e}")
            raise
    
    async def run_complete_setup(self):
        """Run complete setup process"""
        print("🚀 Starting Enhanced AI Interviewer Bot Setup")
        print("=" * 50)
        
        try:
            # Step 1: Database setup
            await self.setup_database()
            
            # Step 2: Populate expected answers
            await self.populate_expected_answers()
            
            # Step 3: Initialize RAG system
            await self.initialize_rag_system()
            
            # Step 4: Initialize ML models
            await self.initialize_ml_models()
            
            # Step 5: Test integration
            await self.test_system_integration()
            
            print("\n🎉 Enhanced AI Interviewer Bot Setup Complete!")
            print("=" * 50)
            print("✅ Database schema created")
            print("✅ Expected answers populated")
            print("✅ RAG system initialized")
            print("✅ ML models trained")
            print("✅ System integration tested")
            print("\n🚀 Ready to start enhanced interviews!")
            
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)

async def main():
    """Main setup function"""
    setup = EnhancedSystemSetup()
    await setup.run_complete_setup()

if __name__ == "__main__":
    asyncio.run(main())
