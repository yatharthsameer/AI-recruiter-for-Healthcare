"""
Simple API server to serve interview data to the admin panel
"""
import os
import json
import glob
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import re

app = FastAPI(title="Interview Data API", version="1.0.0")

# Enable CORS for the admin panel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory containing interview outputs
INTERVIEW_OUTPUTS_DIR = "interview-outputs"

class InterviewDataService:
    """Service to parse and serve interview data"""
    
    @staticmethod
    def get_all_interviews() -> List[Dict[str, Any]]:
        """Get all completed interviews"""
        interviews = []
        
        if not os.path.exists(INTERVIEW_OUTPUTS_DIR):
            return interviews
        
        # Find all evaluation files
        evaluation_files = glob.glob(os.path.join(INTERVIEW_OUTPUTS_DIR, "evaluation_*.txt"))
        
        for eval_file in evaluation_files:
            try:
                # Extract session ID from filename
                session_id = InterviewDataService._extract_session_id(eval_file)
                if not session_id:
                    continue
                
                # Parse evaluation file
                evaluation_data = InterviewDataService._parse_evaluation_file(eval_file)
                
                # Find corresponding transcript file by session ID
                transcript_pattern = os.path.join(INTERVIEW_OUTPUTS_DIR, f"transcript_{session_id}_*.txt")
                transcript_files = glob.glob(transcript_pattern)
                transcript_data = None
                if transcript_files:
                    transcript_file = transcript_files[0]  # Take the first match
                    transcript_data = InterviewDataService._parse_transcript_file(transcript_file, session_id)
                else:
                    print(f"No transcript file found for session {session_id}")
                
                # Combine data
                interview = {
                    "sessionId": session_id,
                    "status": "completed",
                    "interviewType": evaluation_data.get("interviewType", "general"),
                    "userData": evaluation_data.get("userData", {}),
                    "startTime": evaluation_data.get("startTime"),
                    "endTime": evaluation_data.get("endTime"),
                    "duration": evaluation_data.get("duration", 0),
                    "caregiverEvaluation": evaluation_data.get("evaluation", {}),
                    "transcript": transcript_data,
                    "metadata": {
                        "lastActivity": evaluation_data.get("endTime"),
                        "clientIp": "127.0.0.1",  # Default for now
                        "userAgent": "Unknown"
                    }
                }
                
                interviews.append(interview)
                
            except Exception as e:
                print(f"Error processing {eval_file}: {e}")
                continue
        
        # Sort by date (newest first)
        interviews.sort(key=lambda x: x.get("startTime", ""), reverse=True)
        return interviews
    
    @staticmethod
    def get_interview_by_id(session_id: str) -> Optional[Dict[str, Any]]:
        """Get specific interview by session ID"""
        interviews = InterviewDataService.get_all_interviews()
        return next((i for i in interviews if i["sessionId"] == session_id), None)
    
    @staticmethod
    def _extract_session_id(filename: str) -> Optional[str]:
        """Extract session ID from filename"""
        match = re.search(r'evaluation_([a-f0-9\-]+)_', filename)
        return match.group(1) if match else None
    
    @staticmethod
    def _parse_evaluation_file(filepath: str) -> Dict[str, Any]:
        """Parse evaluation text file"""
        data = {
            "userData": {},
            "evaluation": {},
            "interviewType": "general",
            "duration": 0
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract basic info
            if "Candidate:" in content:
                name_match = re.search(r'Candidate:\s*(.+)', content)
                if name_match:
                    full_name = name_match.group(1).strip()
                    name_parts = full_name.split()
                    data["userData"]["firstName"] = name_parts[0] if name_parts else ""
                    data["userData"]["lastName"] = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            if "Email:" in content:
                email_match = re.search(r'Email:\s*(.+)', content)
                if email_match:
                    data["userData"]["email"] = email_match.group(1).strip()
            
            if "Phone:" in content:
                phone_match = re.search(r'Phone:\s*(.+)', content)
                if phone_match:
                    data["userData"]["phone"] = phone_match.group(1).strip()
            
            if "Position Applied:" in content:
                position_match = re.search(r'Position Applied:\s*(.+)', content)
                if position_match:
                    data["userData"]["position"] = position_match.group(1).strip().lower()
            
            if "Interview Type:" in content:
                type_match = re.search(r'Interview Type:\s*(.+)', content)
                if type_match:
                    data["interviewType"] = type_match.group(1).strip().lower()
            
            # Extract overall score
            score_match = re.search(r'Overall Score:\s*(\d+)/100', content)
            if score_match:
                data["evaluation"]["overallScore"] = int(score_match.group(1))
            
            # Extract duration
            duration_match = re.search(r'Duration:\s*([\d.]+)\s*seconds', content)
            if duration_match:
                data["duration"] = float(duration_match.group(1))
            
            # Extract recommendation
            rec_match = re.search(r'\*\*Recommendation:\*\*\s*(.+)', content)
            if rec_match:
                data["evaluation"]["recommendation"] = {
                    "recommendation": rec_match.group(1).strip(),
                    "confidence": "Medium",  # Default
                    "reasoning": "Based on interview performance"
                }
            
            # Extract competency scores (simplified parsing)
            competency_scores = {}
            competency_patterns = {
                "empathy_compassion": r'\*\*Empathy & Compassion:\*\*\s*\[(\d+)/10\]',
                "safety_awareness": r'\*\*Safety Awareness:\*\*\s*\[(\d+)/10\]',
                "communication_skills": r'\*\*Communication Skills:\*\*\s*\[(\d+)/10\]',
                "problem_solving": r'\*\*Problem-Solving:\*\*\s*\[(\d+)/10\]',
                "experience_commitment": r'\*\*Experience & Commitment:\*\*\s*\[(\d+)/10\]'
            }
            
            for key, pattern in competency_patterns.items():
                match = re.search(pattern, content)
                if match:
                    competency_scores[key] = int(match.group(1))
                else:
                    competency_scores[key] = 5  # Default score
            
            data["evaluation"]["competencyScores"] = competency_scores
            
            # Extract strengths and development areas (simplified)
            strengths = []
            dev_areas = []
            
            # Look for bullet points after "KEY STRENGTHS" section
            strengths_section = re.search(r'\*\*3\) KEY STRENGTHS\*\*(.*?)\*\*4\)', content, re.DOTALL)
            if strengths_section:
                strength_matches = re.findall(r'\*\s*\*\*(.+?):\*\*', strengths_section.group(1))
                strengths = [s.strip() for s in strength_matches]
            
            # Look for development areas
            dev_section = re.search(r'\*\*4\) DEVELOPMENT AREAS\*\*(.*?)\*\*5\)', content, re.DOTALL)
            if dev_section:
                dev_matches = re.findall(r'\*\s*\*\*(.+?):\*\*', dev_section.group(1))
                dev_areas = [d.strip() for d in dev_matches]
            
            data["evaluation"]["strengths"] = strengths
            data["evaluation"]["developmentAreas"] = dev_areas
            
            # Extract next steps
            next_steps = []
            steps_section = re.search(r'\*\*7\) NEXT STEPS\*\*(.*?)(?:\*\*|$)', content, re.DOTALL)
            if steps_section:
                step_matches = re.findall(r'\*\s*\*\*(.+?):\*\*', steps_section.group(1))
                next_steps = [s.strip() for s in step_matches]
            
            data["evaluation"]["nextSteps"] = next_steps
            
            # Set timestamps (extract from filename or use current time)
            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})', filepath)
            if timestamp_match:
                timestamp_str = timestamp_match.group(1).replace('-', ':', 2).replace('-', ':')
                try:
                    dt = datetime.fromisoformat(timestamp_str)
                    data["startTime"] = dt.isoformat()
                    data["endTime"] = dt.isoformat()
                except:
                    data["startTime"] = datetime.now().isoformat()
                    data["endTime"] = datetime.now().isoformat()
            else:
                data["startTime"] = datetime.now().isoformat()
                data["endTime"] = datetime.now().isoformat()
            
        except Exception as e:
            print(f"Error parsing evaluation file {filepath}: {e}")
        
        return data
    
    @staticmethod
    def _parse_transcript_file(filepath: str, session_id: str = "unknown") -> Optional[Dict[str, Any]]:
        """Parse transcript text file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            questions = []
            responses = []
            
            # Extract Q&A pairs - updated pattern for actual transcript format
            qa_pattern = r'Q(\d+):\s*(.+?)\n\nA\1:\s*(.+?)(?=\n\n-{40}|\n\n=|$)'
            matches = re.findall(qa_pattern, content, re.DOTALL)
            
            for match in matches:
                question_num = int(match[0])
                question_text = match[1].strip()
                answer_text = match[2].strip()
                
                questions.append({
                    "question": question_text,
                    "questionNumber": question_num,
                    "timestamp": datetime.now().isoformat()  # Would be actual timestamp in real system
                })
                
                responses.append({
                    "response": answer_text,
                    "questionNumber": question_num,
                    "timestamp": datetime.now().isoformat(),
                    "analysis": None  # Would include actual analysis
                })
            
            return {
                "sessionId": session_id,
                "questions": questions,
                "responses": responses,
                "duration": 300  # Default duration
            }
            
        except Exception as e:
            print(f"Error parsing transcript file {filepath}: {e}")
            return None

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Interview Data API", "version": "1.0.0"}

@app.get("/api/interviews")
async def get_interviews():
    """Get all completed interviews"""
    try:
        interviews = InterviewDataService.get_all_interviews()
        return JSONResponse(content=interviews)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interviews/{session_id}")
async def get_interview(session_id: str):
    """Get specific interview by session ID"""
    try:
        interview = InterviewDataService.get_interview_by_id(session_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        return JSONResponse(content=interview)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interviews/{session_id}/transcript")
async def get_transcript(session_id: str):
    """Get transcript for specific interview"""
    try:
        interview = InterviewDataService.get_interview_by_id(session_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        transcript = interview.get("transcript")
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        return JSONResponse(content=transcript)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interviews/{session_id}/evaluation")
async def get_evaluation(session_id: str):
    """Get evaluation for specific interview"""
    try:
        interview = InterviewDataService.get_interview_by_id(session_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        evaluation = interview.get("caregiverEvaluation")
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        return JSONResponse(content=evaluation)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
