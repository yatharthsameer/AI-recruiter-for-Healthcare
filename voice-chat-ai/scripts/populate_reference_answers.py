"""
Script to populate reference answers from JSON file into database and Elasticsearch
Run this to load your correct/wrong answer examples for RAG system
"""

import os
import sys
import json
import asyncio
import asyncpg
from datetime import datetime

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.rag_system import CaregiverRAGSystem

async def populate_reference_answers():
    """Load reference answers from JSON file into database and Elasticsearch"""
    
    # Database connection
    db_connection = os.getenv(
        'DATABASE_URL', 
        'postgresql://interview_admin:secure_password@localhost:5432/interview_bot'
    )
    
    elasticsearch_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
    
    print("📚 Loading reference answers into RAG system...")
    print("=" * 50)
    
    try:
        # Load reference answers from JSON
        json_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'reference_answers.json')
        
        if not os.path.exists(json_file):
            print(f"❌ Reference answers file not found: {json_file}")
            return
        
        with open(json_file, 'r', encoding='utf-8') as f:
            reference_data = json.load(f)
        
        # Initialize RAG system
        rag_system = CaregiverRAGSystem(db_connection, elasticsearch_url)
        
        # Initialize Elasticsearch index
        await rag_system.initialize_elasticsearch_index()
        
        total_answers = 0
        
        # Process each question
        for question_key, question_data in reference_data.items():
            question_id = question_key.split('_')[0]  # Extract Q1, Q7, Q8 etc.
            
            print(f"\n📝 Processing {question_id}: {question_data['question_text'][:60]}...")
            
            # Process each quality level
            for quality_level in ['excellent_answers', 'good_answers', 'fair_answers', 'poor_answers']:
                quality = quality_level.replace('_answers', '')  # excellent, good, fair, poor
                
                if quality_level in question_data:
                    answers = question_data[quality_level]
                    
                    for answer_data in answers:
                        try:
                            # Add to RAG system (this handles both database and Elasticsearch)
                            answer_id = await rag_system.add_expected_answer(
                                question_id=question_id,
                                answer_text=answer_data['text'],
                                quality_level=quality,
                                empathy_indicators=answer_data.get('empathy_indicators', []),
                                experience_indicators=answer_data.get('experience_indicators', []),
                                behavioral_patterns=answer_data.get('behavioral_patterns', [])
                            )
                            
                            print(f"  ✅ Added {quality} answer: {answer_data['id']}")
                            total_answers += 1
                            
                        except Exception as e:
                            print(f"  ❌ Error adding {answer_data['id']}: {e}")
        
        print(f"\n🎉 Successfully loaded {total_answers} reference answers!")
        print("=" * 50)
        
        # Test the system
        print("\n🧪 Testing RAG system with sample answer...")
        test_answer = "I took care of my grandmother with dementia. It was challenging but meaningful."
        
        result = await rag_system.evaluate_answer("Q7", test_answer)
        
        print(f"  📊 Test Result:")
        print(f"     Semantic Score: {result.semantic_similarity_score:.1f}/100")
        print(f"     Quality Match: {result.best_match.quality_level}")
        print(f"     Final Score: {result.final_score:.1f}/100")
        print(f"     Empathy Bonus: {result.empathy_bonus:.2f}x")
        
        print("\n✅ RAG system is working correctly!")
        
    except Exception as e:
        print(f"❌ Error loading reference answers: {e}")
        raise

async def add_single_answer():
    """Interactive function to add a single reference answer"""
    
    print("➕ Add Single Reference Answer")
    print("=" * 30)
    
    # Get input from user
    question_id = input("Question ID (Q1, Q2, Q3, etc.): ").strip()
    quality_level = input("Quality level (excellent, good, fair, poor): ").strip()
    answer_text = input("Answer text: ").strip()
    
    if not all([question_id, quality_level, answer_text]):
        print("❌ All fields are required")
        return
    
    # Database connection
    db_connection = os.getenv(
        'DATABASE_URL', 
        'postgresql://interview_admin:secure_password@localhost:5432/interview_bot'
    )
    elasticsearch_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
    
    try:
        # Initialize RAG system
        rag_system = CaregiverRAGSystem(db_connection, elasticsearch_url)
        
        # Add the answer
        answer_id = await rag_system.add_expected_answer(
            question_id=question_id,
            answer_text=answer_text,
            quality_level=quality_level,
            empathy_indicators=[],  # You can enhance this
            experience_indicators=[],
            behavioral_patterns=[]
        )
        
        print(f"✅ Added answer with ID: {answer_id}")
        
    except Exception as e:
        print(f"❌ Error adding answer: {e}")

async def view_existing_answers():
    """View existing reference answers in the database"""
    
    print("👀 Existing Reference Answers")
    print("=" * 30)
    
    try:
        db_connection = os.getenv(
            'DATABASE_URL', 
            'postgresql://interview_admin:secure_password@localhost:5432/interview_bot'
        )
        
        conn = await asyncpg.connect(db_connection)
        
        # Get summary by question and quality
        summary = await conn.fetch("""
            SELECT question_id, quality_level, COUNT(*) as count
            FROM expected_answers
            GROUP BY question_id, quality_level
            ORDER BY question_id, quality_level
        """)
        
        print(f"📊 Summary of Reference Answers:")
        for row in summary:
            print(f"  {row['question_id']} - {row['quality_level']}: {row['count']} answers")
        
        # Get detailed view
        print(f"\n📝 Detailed View:")
        answers = await conn.fetch("""
            SELECT id, question_id, quality_level, 
                   LEFT(answer_text, 100) as answer_preview,
                   array_length(empathy_indicators, 1) as empathy_count
            FROM expected_answers
            ORDER BY question_id, quality_level, id
            LIMIT 20
        """)
        
        for answer in answers:
            print(f"  {answer['id']}: {answer['question_id']} ({answer['quality_level']})")
            print(f"    Preview: {answer['answer_preview']}...")
            print(f"    Empathy indicators: {answer['empathy_count'] or 0}")
            print()
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error viewing answers: {e}")

def main():
    """Main function with menu options"""
    
    print("🎯 Reference Answers Management")
    print("=" * 35)
    print("1. Load all reference answers from JSON file")
    print("2. Add single reference answer")
    print("3. View existing reference answers")
    print("4. Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        asyncio.run(populate_reference_answers())
    elif choice == "2":
        asyncio.run(add_single_answer())
    elif choice == "3":
        asyncio.run(view_existing_answers())
    elif choice == "4":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
