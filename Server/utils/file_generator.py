"""
File Generation Utilities
Handles creation of interview transcripts and evaluation reports
"""
import os
import logging
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class FileGenerator:
    """Handles generation of interview output files"""
    
    def __init__(self, output_dir: str = "interview-outputs"):
        self.output_dir = Path(output_dir)
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Ensure output directory exists"""
        try:
            self.output_dir.mkdir(exist_ok=True)
            logger.info(f"Output directory ready: {self.output_dir}")
        except Exception as e:
            logger.error(f"Failed to create output directory: {e}")
            raise
    
    async def generate_transcript_file(
        self, 
        session_id: str, 
        transcript: List[Dict], 
        user_data: Dict, 
        summary: Dict
    ) -> str:
        """Generate interview transcript file in JSON format only"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S-%f')[:-3] + 'Z'
            json_filename = f"transcript_{session_id}_{timestamp}.json"
            json_path = self.output_dir / json_filename
            
            json_payload = self._build_transcript_json(session_id, transcript, user_data, summary)
            with open(json_path, 'w', encoding='utf-8') as jf:
                json.dump(json_payload, jf, ensure_ascii=False, indent=2)
            
            logger.info(f"Generated transcript JSON file: {json_filename}")
            return str(json_path)
            
        except Exception as e:
            logger.error(f"Failed to generate transcript file: {e}")
            raise
    
    async def generate_evaluation_file(
        self, 
        session_id: str, 
        evaluation: Dict, 
        user_data: Dict, 
        caregiver_evaluation: Optional[Dict] = None
    ) -> str:
        """Generate evaluation report file in JSON format only"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S-%f')[:-3] + 'Z'
            json_filename = f"evaluation_{session_id}_{timestamp}.json"
            json_path = self.output_dir / json_filename
            
            payload = self._build_evaluation_json(session_id, user_data, evaluation, caregiver_evaluation)
            with open(json_path, 'w', encoding='utf-8') as jf:
                json.dump(payload, jf, ensure_ascii=False, indent=2)
            
            logger.info(f"Generated evaluation JSON file: {json_filename}")
            return str(json_path)
            
        except Exception as e:
            logger.error(f"Failed to generate evaluation file: {e}")
            raise
    
    async def generate_interview_files(
        self, 
        session_id: str, 
        transcript: List[Dict], 
        user_data: Dict, 
        summary: Dict, 
        caregiver_evaluation: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Generate both transcript and evaluation files"""
        try:
            files = {}
            
            # Generate transcript file
            transcript_path = await self.generate_transcript_file(
                session_id, transcript, user_data, summary
            )
            files['transcript'] = transcript_path
            
            # Generate evaluation file if we have evaluation data
            if caregiver_evaluation or summary.get('finalFeedback'):
                evaluation_path = await self.generate_evaluation_file(
                    session_id, summary, user_data, caregiver_evaluation
                )
                files['evaluation'] = evaluation_path
            
            logger.info(f"Generated {len(files)} files for session {session_id}")
            return files
            
        except Exception as e:
            logger.error(f"Failed to generate interview files: {e}")
            return {}
    
    def _build_transcript_content(
        self, 
        session_id: str, 
        transcript: List[Dict], 
        user_data: Dict, 
        summary: Dict
    ) -> str:
        """Build transcript file content"""
        
        now = datetime.now()
        
        content = f"""============================================================
                    INTERVIEW TRANSCRIPT
============================================================

Session ID: {session_id}
Date: {now.strftime('%d/%m/%Y, %I:%M:%S %p')}
Candidate: {user_data.get('firstName', '')} {user_data.get('lastName', '')}
Email: {user_data.get('email', '')}
Position: {user_data.get('position', '')}
Phone: {user_data.get('phone', '')}

------------------------------------------------------------
                    QUESTIONS & ANSWERS
------------------------------------------------------------
"""
        
        # Add Q&A pairs
        for item in transcript:
            q_num = item.get('questionNumber', 0)
            question = item.get('question', '')
            response = item.get('userResponse', '[No response recorded]')
            
            content += f"\nQ{q_num}: {question}\n\n"
            content += f"A{q_num}: {response}\n\n"
            content += "----------------------------------------\n"
        
        # Add summary if available
        final_feedback = summary.get('finalFeedback', '')
        if final_feedback:
            content += f"""
============================================================
                    INTERVIEW SUMMARY
============================================================

{final_feedback}
"""
        
        content += f"""
============================================================
Generated on: {now.strftime('%d/%m/%Y, %I:%M:%S %p')}
============================================================
"""
        
        return content

    def _build_transcript_json(
        self,
        session_id: str,
        transcript: List[Dict],
        user_data: Dict,
        summary: Dict
    ) -> Dict:
        """Build structured JSON transcript capturing questions, responses, and audio paths."""
        # Build questions/responses arrays
        questions: List[Dict] = []
        responses: List[Dict] = []
        for item in transcript:
            q_num = item.get('questionNumber', 0)
            questions.append({
                "question": item.get('question', ''),
                "questionNumber": q_num,
                "timestamp": item.get('questionTimestamp') or datetime.now().isoformat()
            })
            
            # Build response with proper audio path and analysis
            response_data = {
                "response": item.get('userResponse', ''),
                "questionNumber": q_num,
                "timestamp": item.get('responseTimestamp') or datetime.now().isoformat(),
                "audioPath": item.get('audioPath'),  # Relative path like "audio/filename.wav"
            }
            
            # Add analysis if available (for competency scoring)
            analysis = item.get('analysis')
            if analysis:
                response_data["analysis"] = {
                    "scoreImpact": analysis.get('scoreImpact', {}),
                    "flags": analysis.get('flags', []),
                    "keyTerms": analysis.get('keyTerms', [])
                }
            
            responses.append(response_data)

        result: Dict = {
            "sessionId": session_id,
            "questions": questions,
            "responses": responses,
            "duration": summary.get('duration', 0),
            "metadata": {
                "startTime": summary.get('startTime'),
                "endTime": summary.get('endTime'),
                "userData": user_data,
            }
        }
        return result
    
    def _build_evaluation_content(
        self, 
        session_id: str, 
        summary: Dict, 
        user_data: Dict, 
        caregiver_evaluation: Optional[Dict] = None
    ) -> str:
        """Build evaluation file content"""
        
        now = datetime.now()
        
        # Use caregiver evaluation if available, otherwise use general summary
        if caregiver_evaluation and summary.get('role') == 'home_care':
            return self._build_caregiver_evaluation_content(
                session_id, user_data, caregiver_evaluation, now
            )
        else:
            return self._build_general_evaluation_content(
                session_id, summary, user_data, now
            )
    
    def _build_caregiver_evaluation_content(
        self, 
        session_id: str, 
        user_data: Dict, 
        caregiver_evaluation: Dict, 
        timestamp: datetime
    ) -> str:
        """Build caregiver-specific evaluation content"""
        
        content = f"""================================================================================
                    FIRSTLIGHT HOME CARE - CAREGIVER EVALUATION
================================================================================

Session ID: {session_id}
Evaluation Date: {timestamp.strftime('%d/%m/%Y, %I:%M:%S %p')}
Candidate: {user_data.get('firstName', '')} {user_data.get('lastName', '')}
Email: {user_data.get('email', '')}
Phone: {user_data.get('phone', '')}
Position Applied: {user_data.get('position', '')}

------------------------------------------------------------
                    CANDIDATE BACKGROUND
------------------------------------------------------------

HHA Experience: {'Yes' if user_data.get('hhaExperience') else 'No'}
CPR Certified: {'Yes' if user_data.get('cprCertified') else 'No'}
Driver's License: {'Yes' if user_data.get('driversLicense') else 'No'}
Auto Insurance: {'Yes' if user_data.get('autoInsurance') else 'No'}
Reliable Transport: {'Yes' if user_data.get('reliableTransport') else 'No'}
Availability: {', '.join(user_data.get('availability', []))}
Preferred Hours/Week: {user_data.get('weeklyHours', 'Not specified')}
Location Preference: {user_data.get('locationPref', 'Not specified')}

================================================================================
                    AI DETAILED ANALYSIS
================================================================================
"""
        
        # Add competency scores
        competency_scores = caregiver_evaluation.get('competencyScores', {})
        if competency_scores:
            content += "\n**COMPETENCY SCORES:**\n\n"
            
            score_labels = {
                'empathy_compassion': 'Empathy & Compassion',
                'safety_awareness': 'Safety Awareness',
                'communication_skills': 'Communication Skills',
                'problem_solving': 'Problem-Solving',
                'experience_commitment': 'Experience & Commitment'
            }
            
            for key, label in score_labels.items():
                score = competency_scores.get(key, 0)
                content += f"*   **{label}:** {score}/10\n"
        
        # Add strengths
        strengths = caregiver_evaluation.get('strengths', [])
        if strengths:
            content += "\n\n**KEY STRENGTHS:**\n\n"
            for strength in strengths:
                content += f"*   {strength}\n"
        
        # Add development areas
        development_areas = caregiver_evaluation.get('developmentAreas', [])
        if development_areas:
            content += "\n\n**DEVELOPMENT AREAS:**\n\n"
            for area in development_areas:
                content += f"*   {area}\n"
        
        # Add recommendation
        recommendation = caregiver_evaluation.get('recommendation', {})
        if recommendation:
            content += f"\n\n**HIRING RECOMMENDATION:**\n\n"
            content += f"{recommendation.get('recommendation', 'Not specified')}\n"
            
            reasoning = recommendation.get('reasoning', '')
            if reasoning:
                content += f"\n**REASONING:**\n{reasoning}\n"
        
        # Add next steps
        next_steps = caregiver_evaluation.get('nextSteps', [])
        if next_steps:
            content += "\n\n**NEXT STEPS:**\n\n"
            for i, step in enumerate(next_steps, 1):
                content += f"{i}. {step}\n"
        
        content += f"""
================================================================================
Report Generated: {timestamp.strftime('%d/%m/%Y, %I:%M:%S %p')}
FirstLight Home Care - AI Interview Evaluation System v2.0
================================================================================
"""
        
        return content
    
    def _build_general_evaluation_content(
        self, 
        session_id: str, 
        summary: Dict, 
        user_data: Dict, 
        timestamp: datetime
    ) -> str:
        """Build general evaluation content"""
        
        content = f"""================================================================================
                    INTERVIEW EVALUATION REPORT
================================================================================

Session ID: {session_id}
Evaluation Date: {timestamp.strftime('%d/%m/%Y, %I:%M:%S %p')}
Candidate: {user_data.get('firstName', '')} {user_data.get('lastName', '')}
Email: {user_data.get('email', '')}
Phone: {user_data.get('phone', '')}
Position Applied: {user_data.get('position', '')}
Interview Type: {summary.get('role', 'General')}

================================================================================
                    EVALUATION SUMMARY
================================================================================

Overall Score: {summary.get('score', 'N/A')}/100
Duration: {summary.get('duration', 'N/A')} seconds
Questions Answered: {summary.get('questionsCount', 0)}

"""
        
        # Add final feedback if available
        final_feedback = summary.get('finalFeedback', '')
        if final_feedback:
            content += f"""
================================================================================
                    DETAILED FEEDBACK
================================================================================

{final_feedback}
"""
        
        content += f"""
================================================================================
Report Generated: {timestamp.strftime('%d/%m/%Y, %I:%M:%S %p')}
AI Interview Evaluation System
================================================================================
"""
        
        return content

    def _build_evaluation_json(
        self,
        session_id: str,
        user_data: Dict,
        summary: Dict,
        caregiver_evaluation: Optional[Dict] = None
    ) -> Dict:
        ts = datetime.now().isoformat()
        if caregiver_evaluation:
            data = {
                "sessionId": session_id,
                "timestamp": ts,
                "overallScore": caregiver_evaluation.get("overallScore"),
                "recommendation": caregiver_evaluation.get("recommendation"),
                "competencyScores": caregiver_evaluation.get("competencyScores", {}),
                "strengths": caregiver_evaluation.get("strengths", []),
                "developmentAreas": caregiver_evaluation.get("developmentAreas", []),
                "nextSteps": caregiver_evaluation.get("nextSteps", []),
            }
        else:
            data = {
                "sessionId": session_id,
                "timestamp": ts,
                "overallScore": summary.get("score"),
                "recommendation": summary.get("recommendation"),
                "competencyScores": summary.get("competencyScores", {}),
                "strengths": summary.get("strengths", []),
                "developmentAreas": summary.get("developmentAreas", []),
                "nextSteps": summary.get("nextSteps", []),
            }
        data["userData"] = {
            "firstName": user_data.get("firstName"),
            "lastName": user_data.get("lastName"),
            "email": user_data.get("email"),
            "phone": user_data.get("phone"),
            "position": user_data.get("position"),
        }
        return data
    
    def list_output_files(self) -> List[Dict]:
        """List all generated output files (JSON only)"""
        try:
            files = []
            
            if not self.output_dir.exists():
                return files
            
            for file_path in self.output_dir.iterdir():
                if file_path.is_file() and file_path.suffix == '.json':
                    stat = file_path.stat()
                    files.append({
                        'filename': file_path.name,
                        'path': str(file_path),
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # Sort by creation time, newest first
            files.sort(key=lambda x: x['created'], reverse=True)
            return files
            
        except Exception as e:
            logger.error(f"Failed to list output files: {e}")
            return []
    
    def cleanup_old_files(self, days_old: int = 30) -> int:
        """Clean up files older than specified days"""
        try:
            if not self.output_dir.exists():
                return 0
            
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            deleted_count = 0
            
            for file_path in self.output_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
            return 0

# Global instance
file_generator = FileGenerator()
