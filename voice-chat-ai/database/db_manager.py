"""
Database Manager for Reference Answers
Direct database operations for managing reference Q&A
"""

import os
import json
import asyncio
import asyncpg
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReferenceAnswerDB:
    """Database manager for reference answers"""
    
    def __init__(self, db_connection_string: str):
        self.db_connection_string = db_connection_string
    
    async def add_reference_answer(self, question_id: str, answer_text: str, 
                                 quality_level: str, empathy_indicators: List[str] = None,
                                 experience_indicators: List[str] = None,
                                 behavioral_patterns: List[str] = None) -> str:
        """Add a new reference answer directly to database"""
        
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Generate unique ID
            answer_id = f"{question_id}_{quality_level}_{hash(answer_text) % 10000:04d}"
            
            # Determine score range based on quality
            score_ranges = {
                'excellent': (90, 100),
                'good': (75, 89),
                'fair': (60, 74),
                'poor': (0, 59)
            }
            score_min, score_max = score_ranges.get(quality_level, (50, 70))
            
            # Default empty lists if not provided
            empathy_indicators = empathy_indicators or []
            experience_indicators = experience_indicators or []
            behavioral_patterns = behavioral_patterns or []
            
            # Insert into database
            await conn.execute("""
                INSERT INTO expected_answers (
                    id, question_id, answer_text, quality_level, 
                    score_range_min, score_range_max,
                    empathy_indicators, experience_indicators, behavioral_patterns,
                    embedding_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, 
            answer_id, question_id, answer_text, quality_level, 
            score_min, score_max,
            json.dumps(empathy_indicators), 
            json.dumps(experience_indicators),
            json.dumps(behavioral_patterns),
            f"{answer_id}_embedding")
            
            await conn.close()
            logger.info(f"Added reference answer: {answer_id}")
            return answer_id
            
        except Exception as e:
            logger.error(f"Error adding reference answer: {e}")
            raise
    
    async def get_reference_answers(self, question_id: str = None, 
                                  quality_level: str = None) -> List[Dict]:
        """Get reference answers with optional filtering"""
        
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Build query with optional filters
            where_conditions = []
            params = []
            param_count = 0
            
            if question_id:
                param_count += 1
                where_conditions.append(f"question_id = ${param_count}")
                params.append(question_id)
            
            if quality_level:
                param_count += 1
                where_conditions.append(f"quality_level = ${param_count}")
                params.append(quality_level)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            query = f"""
                SELECT id, question_id, answer_text, quality_level,
                       score_range_min, score_range_max,
                       empathy_indicators, experience_indicators, behavioral_patterns,
                       created_at
                FROM expected_answers
                {where_clause}
                ORDER BY question_id, quality_level, created_at
            """
            
            results = await conn.fetch(query, *params)
            await conn.close()
            
            return [
                {
                    'id': row['id'],
                    'question_id': row['question_id'],
                    'answer_text': row['answer_text'],
                    'quality_level': row['quality_level'],
                    'score_range': [row['score_range_min'], row['score_range_max']],
                    'empathy_indicators': row['empathy_indicators'],
                    'experience_indicators': row['experience_indicators'],
                    'behavioral_patterns': row['behavioral_patterns'],
                    'created_at': row['created_at'].isoformat()
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting reference answers: {e}")
            return []
    
    async def update_reference_answer(self, answer_id: str, **updates) -> bool:
        """Update an existing reference answer"""
        
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Build update query dynamically
            update_fields = []
            params = []
            param_count = 0
            
            for field, value in updates.items():
                if field in ['answer_text', 'quality_level', 'empathy_indicators', 
                           'experience_indicators', 'behavioral_patterns']:
                    param_count += 1
                    update_fields.append(f"{field} = ${param_count}")
                    
                    # JSON encode lists
                    if field.endswith('_indicators') or field.endswith('_patterns'):
                        params.append(json.dumps(value) if isinstance(value, list) else value)
                    else:
                        params.append(value)
            
            if not update_fields:
                return False
            
            param_count += 1
            params.append(answer_id)
            
            query = f"""
                UPDATE expected_answers 
                SET {', '.join(update_fields)}
                WHERE id = ${param_count}
            """
            
            result = await conn.execute(query, *params)
            await conn.close()
            
            return result == "UPDATE 1"
            
        except Exception as e:
            logger.error(f"Error updating reference answer: {e}")
            return False
    
    async def delete_reference_answer(self, answer_id: str) -> bool:
        """Delete a reference answer"""
        
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            result = await conn.execute("""
                DELETE FROM expected_answers WHERE id = $1
            """, answer_id)
            
            await conn.close()
            
            return result == "DELETE 1"
            
        except Exception as e:
            logger.error(f"Error deleting reference answer: {e}")
            return False
    
    async def get_questions_summary(self) -> Dict:
        """Get summary of reference answers by question and quality"""
        
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            summary = await conn.fetch("""
                SELECT 
                    question_id,
                    quality_level,
                    COUNT(*) as count,
                    AVG((score_range_min + score_range_max) / 2) as avg_score
                FROM expected_answers
                GROUP BY question_id, quality_level
                ORDER BY question_id, quality_level
            """)
            
            total_count = await conn.fetchval("SELECT COUNT(*) FROM expected_answers")
            
            await conn.close()
            
            # Organize by question
            questions = {}
            for row in summary:
                q_id = row['question_id']
                if q_id not in questions:
                    questions[q_id] = {}
                
                questions[q_id][row['quality_level']] = {
                    'count': row['count'],
                    'avg_score': float(row['avg_score'])
                }
            
            return {
                'total_answers': total_count,
                'questions': questions
            }
            
        except Exception as e:
            logger.error(f"Error getting questions summary: {e}")
            return {}
    
    async def bulk_insert_from_data(self, reference_data: Dict) -> int:
        """Bulk insert reference answers from structured data"""
        
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            inserted_count = 0
            
            for question_key, question_data in reference_data.items():
                question_id = question_key.split('_')[0]  # Extract Q1, Q7, etc.
                
                # Process each quality level
                for quality_level in ['excellent_answers', 'good_answers', 'fair_answers', 'poor_answers']:
                    quality = quality_level.replace('_answers', '')
                    
                    if quality_level in question_data:
                        answers = question_data[quality_level]
                        
                        for answer_data in answers:
                            try:
                                # Determine score range
                                score_ranges = {
                                    'excellent': (90, 100),
                                    'good': (75, 89),
                                    'fair': (60, 74),
                                    'poor': (0, 59)
                                }
                                score_min, score_max = score_ranges[quality]
                                
                                await conn.execute("""
                                    INSERT INTO expected_answers (
                                        id, question_id, answer_text, quality_level,
                                        score_range_min, score_range_max,
                                        empathy_indicators, experience_indicators, behavioral_patterns,
                                        embedding_id
                                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                                    ON CONFLICT (id) DO NOTHING
                                """,
                                answer_data['id'], question_id, answer_data['text'], quality,
                                score_min, score_max,
                                json.dumps(answer_data.get('empathy_indicators', [])),
                                json.dumps(answer_data.get('experience_indicators', [])),
                                json.dumps(answer_data.get('behavioral_patterns', [])),
                                f"{answer_data['id']}_embedding")
                                
                                inserted_count += 1
                                
                            except Exception as e:
                                logger.error(f"Error inserting {answer_data['id']}: {e}")
            
            await conn.close()
            logger.info(f"Bulk inserted {inserted_count} reference answers")
            return inserted_count
            
        except Exception as e:
            logger.error(f"Error in bulk insert: {e}")
            return 0

# CLI functions for easy management
async def cli_add_answer():
    """Command line interface to add reference answer"""
    
    print("➕ Add Reference Answer to Database")
    print("=" * 35)
    
    # Get inputs
    question_id = input("Question ID (Q1-Q9): ").strip().upper()
    if question_id not in [f'Q{i}' for i in range(1, 10)]:
        print("❌ Invalid question ID. Use Q1-Q9")
        return
    
    print("\nQuality levels:")
    print("  excellent (90-100 points) - Detailed, empathetic, professional")
    print("  good (75-89 points) - Some detail, moderate empathy")
    print("  fair (60-74 points) - Basic response, limited empathy")
    print("  poor (0-59 points) - Vague, no empathy, inappropriate")
    
    quality_level = input("\nQuality level: ").strip().lower()
    if quality_level not in ['excellent', 'good', 'fair', 'poor']:
        print("❌ Invalid quality level")
        return
    
    print(f"\nEnter the reference answer for {question_id} ({quality_level}):")
    answer_text = input().strip()
    
    if not answer_text:
        print("❌ Answer text is required")
        return
    
    # Optional indicators
    empathy_input = input("Empathy indicators (comma-separated, optional): ").strip()
    empathy_indicators = [x.strip() for x in empathy_input.split(',') if x.strip()]
    
    experience_input = input("Experience indicators (comma-separated, optional): ").strip()
    experience_indicators = [x.strip() for x in experience_input.split(',') if x.strip()]
    
    behavioral_input = input("Behavioral patterns (comma-separated, optional): ").strip()
    behavioral_patterns = [x.strip() for x in behavioral_input.split(',') if x.strip()]
    
    # Add to database
    try:
        db_connection = os.getenv(
            'DATABASE_URL', 
            'postgresql://interview_admin:secure_password@localhost:5432/interview_bot'
        )
        
        db_manager = ReferenceAnswerDB(db_connection)
        
        answer_id = await db_manager.add_reference_answer(
            question_id, answer_text, quality_level,
            empathy_indicators, experience_indicators, behavioral_patterns
        )
        
        print(f"\n✅ Successfully added reference answer: {answer_id}")
        
    except Exception as e:
        print(f"\n❌ Error adding reference answer: {e}")

async def cli_view_answers():
    """Command line interface to view reference answers"""
    
    print("👀 View Reference Answers")
    print("=" * 25)
    
    question_id = input("Question ID (Q1-Q9, or leave empty for all): ").strip().upper()
    quality_level = input("Quality level (excellent/good/fair/poor, or leave empty for all): ").strip().lower()
    
    try:
        db_connection = os.getenv(
            'DATABASE_URL', 
            'postgresql://interview_admin:secure_password@localhost:5432/interview_bot'
        )
        
        db_manager = ReferenceAnswerDB(db_connection)
        
        # Get summary first
        summary = await db_manager.get_questions_summary()
        
        print(f"\n📊 Summary: {summary['total_answers']} total reference answers")
        print("-" * 50)
        
        for q_id, qualities in summary['questions'].items():
            if not question_id or q_id == question_id:
                print(f"\n{q_id}:")
                for qual, data in qualities.items():
                    if not quality_level or qual == quality_level:
                        print(f"  {qual}: {data['count']} answers (avg score: {data['avg_score']:.1f})")
        
        # Get detailed answers if specific filters
        if question_id or quality_level:
            print(f"\n📝 Detailed Answers:")
            print("-" * 30)
            
            answers = await db_manager.get_reference_answers(
                question_id if question_id else None,
                quality_level if quality_level else None
            )
            
            for answer in answers[:10]:  # Limit to 10 for readability
                print(f"\n{answer['id']} ({answer['quality_level']}):")
                print(f"  Text: {answer['answer_text'][:100]}...")
                print(f"  Score Range: {answer['score_range'][0]}-{answer['score_range'][1]}")
                if answer['empathy_indicators']:
                    print(f"  Empathy: {', '.join(answer['empathy_indicators'])}")
        
    except Exception as e:
        print(f"❌ Error viewing answers: {e}")

async def cli_load_seed_data():
    """Load seed data from SQL file"""
    
    print("📚 Loading Seed Reference Answers")
    print("=" * 33)
    
    try:
        db_connection = os.getenv(
            'DATABASE_URL', 
            'postgresql://interview_admin:secure_password@localhost:5432/interview_bot'
        )
        
        # Read seed SQL file
        seed_file = os.path.join(os.path.dirname(__file__), 'seed_reference_answers.sql')
        
        if not os.path.exists(seed_file):
            print(f"❌ Seed file not found: {seed_file}")
            return
        
        with open(seed_file, 'r', encoding='utf-8') as f:
            seed_sql = f.read()
        
        # Execute seed SQL
        conn = await asyncpg.connect(db_connection)
        await conn.execute(seed_sql)
        await conn.close()
        
        print("✅ Seed reference answers loaded successfully!")
        
        # Show summary
        db_manager = ReferenceAnswerDB(db_connection)
        summary = await db_manager.get_questions_summary()
        
        print(f"\n📊 Loaded {summary['total_answers']} reference answers:")
        for q_id, qualities in summary['questions'].items():
            print(f"  {q_id}: {sum(q['count'] for q in qualities.values())} answers")
            for qual, data in qualities.items():
                print(f"    - {qual}: {data['count']}")
        
    except Exception as e:
        print(f"❌ Error loading seed data: {e}")

def main():
    """Main CLI interface"""
    
    print("🗄️  Database Reference Answer Manager")
    print("=" * 38)
    print("1. Load seed reference answers (recommended first step)")
    print("2. Add new reference answer")
    print("3. View existing reference answers")
    print("4. View summary statistics")
    print("5. Exit")
    
    choice = input("\nSelect option (1-5): ").strip()
    
    if choice == "1":
        asyncio.run(cli_load_seed_data())
    elif choice == "2":
        asyncio.run(cli_add_answer())
    elif choice == "3":
        asyncio.run(cli_view_answers())
    elif choice == "4":
        async def show_summary():
            db_manager = ReferenceAnswerDB(os.getenv('DATABASE_URL'))
            summary = await db_manager.get_questions_summary()
            print(json.dumps(summary, indent=2))
        asyncio.run(show_summary())
    elif choice == "5":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
