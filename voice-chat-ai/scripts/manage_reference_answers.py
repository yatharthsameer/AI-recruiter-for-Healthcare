"""
Web-based Reference Answer Management
Provides a simple web interface to add/edit reference answers
"""

import os
import sys
import json
import asyncio
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import asyncpg

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.rag_system import CaregiverRAGSystem

# Initialize FastAPI app for management
app = FastAPI(title="Reference Answers Management", description="Manage reference Q&A for RAG system")

# Templates
templates = Jinja2Templates(directory="templates")

# Global RAG system
rag_system = None

@app.on_event("startup")
async def startup():
    global rag_system
    
    db_connection = os.getenv(
        'DATABASE_URL', 
        'postgresql://interview_admin:secure_password@localhost:5432/interview_bot'
    )
    elasticsearch_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
    
    rag_system = CaregiverRAGSystem(db_connection, elasticsearch_url)
    await rag_system.initialize_elasticsearch_index()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard for reference answer management"""
    
    try:
        # Get summary statistics
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        
        summary = await conn.fetch("""
            SELECT question_id, quality_level, COUNT(*) as count
            FROM expected_answers
            GROUP BY question_id, quality_level
            ORDER BY question_id, quality_level
        """)
        
        total_answers = await conn.fetchval("SELECT COUNT(*) FROM expected_answers")
        
        await conn.close()
        
        # Group by question
        questions_summary = {}
        for row in summary:
            q_id = row['question_id']
            if q_id not in questions_summary:
                questions_summary[q_id] = {}
            questions_summary[q_id][row['quality_level']] = row['count']
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "questions_summary": questions_summary,
            "total_answers": total_answers
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/add", response_class=HTMLResponse)
async def add_answer_form(request: Request):
    """Form to add new reference answer"""
    
    questions = {
        'Q1': 'Have you ever worked as a caregiver? What patients/services?',
        'Q2': 'What traits would you want in a caregiver for your loved one?',
        'Q3': 'How has your experience helped you build caregiver skills?',
        'Q4': 'Why do you want to be a caregiver? Most rewarding aspects?',
        'Q5': 'Time when being late caused problems? What did you learn?',
        'Q6': 'Adjusted routine to ensure punctuality? What changes?',
        'Q7': 'Cared for a senior? Most difficult and meaningful parts?',
        'Q8': 'Helped colleague/client struggling emotionally? What did you do?',
        'Q9': 'What would coworkers say about you? Three things?'
    }
    
    return templates.TemplateResponse("add_answer.html", {
        "request": request,
        "questions": questions
    })

@app.post("/add")
async def add_answer(
    question_id: str = Form(...),
    quality_level: str = Form(...),
    answer_text: str = Form(...),
    empathy_indicators: str = Form(""),
    experience_indicators: str = Form(""),
    behavioral_patterns: str = Form("")
):
    """Add new reference answer"""
    
    try:
        # Parse indicators (comma-separated)
        empathy_list = [x.strip() for x in empathy_indicators.split(',') if x.strip()]
        experience_list = [x.strip() for x in experience_indicators.split(',') if x.strip()]
        behavioral_list = [x.strip() for x in behavioral_patterns.split(',') if x.strip()]
        
        # Add to RAG system
        answer_id = await rag_system.add_expected_answer(
            question_id=question_id,
            answer_text=answer_text,
            quality_level=quality_level,
            empathy_indicators=empathy_list,
            experience_indicators=experience_list,
            behavioral_patterns=behavioral_list
        )
        
        return RedirectResponse(url="/?success=1", status_code=303)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/view/{question_id}", response_class=HTMLResponse)
async def view_question_answers(request: Request, question_id: str):
    """View all answers for a specific question"""
    
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        
        answers = await conn.fetch("""
            SELECT id, answer_text, quality_level, score_range_min, score_range_max,
                   empathy_indicators, experience_indicators, behavioral_patterns,
                   created_at
            FROM expected_answers
            WHERE question_id = $1
            ORDER BY quality_level, created_at
        """, question_id)
        
        await conn.close()
        
        return templates.TemplateResponse("view_answers.html", {
            "request": request,
            "question_id": question_id,
            "answers": answers
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test", response_class=HTMLResponse)
async def test_rag_form(request: Request):
    """Form to test RAG system with candidate answers"""
    
    questions = {
        'Q1': 'Have you ever worked as a caregiver?',
        'Q2': 'What traits would you want in a caregiver?',
        'Q3': 'How has your experience built caregiver skills?',
        'Q4': 'Why do you want to be a caregiver?',
        'Q5': 'Time when being late caused problems?',
        'Q6': 'Adjusted routine for punctuality?',
        'Q7': 'Cared for a senior? Difficult/meaningful?',
        'Q8': 'Helped struggling colleague/client?',
        'Q9': 'What would coworkers say about you?'
    }
    
    return templates.TemplateResponse("test_rag.html", {
        "request": request,
        "questions": questions
    })

@app.post("/test")
async def test_rag_evaluation(
    question_id: str = Form(...),
    candidate_answer: str = Form(...)
):
    """Test RAG evaluation with candidate answer"""
    
    try:
        # Evaluate answer using RAG
        result = await rag_system.evaluate_answer(question_id, candidate_answer)
        
        return {
            "question_id": question_id,
            "candidate_answer": candidate_answer,
            "evaluation": {
                "semantic_similarity_score": result.semantic_similarity_score,
                "final_score": result.final_score,
                "best_match_quality": result.best_match.quality_level,
                "empathy_bonus": result.empathy_bonus,
                "patient_story_bonus": result.patient_story_bonus,
                "care_experience_bonus": result.care_experience_bonus,
                "dignity_mention_bonus": result.dignity_mention_bonus,
                "confidence_level": result.confidence_level
            },
            "best_match_preview": result.best_match.answer_text[:200] + "..."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Create HTML templates directory and files
def create_templates():
    """Create HTML templates for the web interface"""
    
    templates_dir = "templates"
    os.makedirs(templates_dir, exist_ok=True)
    
    # Dashboard template
    dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Reference Answers Management</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .question-card { background: white; border: 1px solid #ddd; padding: 15px; border-radius: 8px; }
        .quality-excellent { color: #28a745; font-weight: bold; }
        .quality-good { color: #17a2b8; }
        .quality-fair { color: #ffc107; }
        .quality-poor { color: #dc3545; }
        .nav { margin: 20px 0; }
        .nav a { margin-right: 15px; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Reference Answers Management</h1>
        <p>Manage correct and incorrect answers for RAG system training</p>
        <p><strong>Total Answers:</strong> {{ total_answers }}</p>
    </div>
    
    <div class="nav">
        <a href="/add">➕ Add New Answer</a>
        <a href="/test">🧪 Test RAG System</a>
    </div>
    
    <h2>📊 Questions Summary</h2>
    <div class="summary">
        {% for question_id, qualities in questions_summary.items() %}
        <div class="question-card">
            <h3>{{ question_id }}</h3>
            <a href="/view/{{ question_id }}">View Details</a>
            <ul>
                {% if qualities.get('excellent') %}
                <li class="quality-excellent">Excellent: {{ qualities.excellent }}</li>
                {% endif %}
                {% if qualities.get('good') %}
                <li class="quality-good">Good: {{ qualities.good }}</li>
                {% endif %}
                {% if qualities.get('fair') %}
                <li class="quality-fair">Fair: {{ qualities.fair }}</li>
                {% endif %}
                {% if qualities.get('poor') %}
                <li class="quality-poor">Poor: {{ qualities.poor }}</li>
                {% endif %}
            </ul>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""
    
    with open(os.path.join(templates_dir, "dashboard.html"), 'w') as f:
        f.write(dashboard_html)
    
    # Add form template
    add_form_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Add Reference Answer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        textarea { height: 150px; }
        button { background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .nav a { color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="nav"><a href="/">← Back to Dashboard</a></div>
    
    <h1>➕ Add Reference Answer</h1>
    
    <form method="post">
        <div class="form-group">
            <label>Question:</label>
            <select name="question_id" required>
                {% for q_id, q_text in questions.items() %}
                <option value="{{ q_id }}">{{ q_id }}: {{ q_text }}</option>
                {% endfor %}
            </select>
        </div>
        
        <div class="form-group">
            <label>Quality Level:</label>
            <select name="quality_level" required>
                <option value="excellent">Excellent (90-100 points)</option>
                <option value="good">Good (75-89 points)</option>
                <option value="fair">Fair (60-74 points)</option>
                <option value="poor">Poor (0-59 points)</option>
            </select>
        </div>
        
        <div class="form-group">
            <label>Answer Text:</label>
            <textarea name="answer_text" placeholder="Enter the reference answer text..." required></textarea>
        </div>
        
        <div class="form-group">
            <label>Empathy Indicators (comma-separated):</label>
            <input type="text" name="empathy_indicators" placeholder="patience, compassion, dignity, understanding">
        </div>
        
        <div class="form-group">
            <label>Experience Indicators (comma-separated):</label>
            <input type="text" name="experience_indicators" placeholder="professional_experience, specific_skills, training">
        </div>
        
        <div class="form-group">
            <label>Behavioral Patterns (comma-separated):</label>
            <input type="text" name="behavioral_patterns" placeholder="STAR_method, problem_solving, specific_examples">
        </div>
        
        <button type="submit">Add Reference Answer</button>
    </form>
</body>
</html>
"""
    
    with open(os.path.join(templates_dir, "add_answer.html"), 'w') as f:
        f.write(add_form_html)
    
    print("✅ Templates created in templates/ directory")

if __name__ == "__main__":
    # Create templates first
    create_templates()
    
    print("🌐 Starting Reference Answers Management Web Interface")
    print("=" * 55)
    print("📋 Available at: http://localhost:8080")
    print("🔧 Use this interface to:")
    print("   - Add excellent/good/fair/poor reference answers")
    print("   - View existing answers by question")
    print("   - Test RAG evaluation with sample answers")
    print("")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
