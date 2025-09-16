"""
Interview Session Model
Manages interview state, questions, responses, and metadata
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

class InterviewStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active" 
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class UserData:
    """User application data"""
    firstName: str = ""
    lastName: str = ""
    email: str = ""
    phone: str = ""
    position: str = ""
    hhaExperience: bool = False
    cprCertified: bool = False
    driversLicense: bool = False
    autoInsurance: bool = False
    reliableTransport: bool = False
    locationPref: str = ""
    availability: List[str] = field(default_factory=list)
    weeklyHours: int = 0

@dataclass
class QuestionData:
    """Interview question data"""
    question: str
    questionNumber: int
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ResponseData:
    """User response data"""
    response: str
    questionNumber: int
    timestamp: datetime = field(default_factory=datetime.now)
    analysis: Optional[str] = None
    audioPath: Optional[str] = None

@dataclass
class ScoringBreakdown:
    """Detailed scoring breakdown for caregiver evaluation"""
    questionNumber: int
    delta: float
    breakdown: Dict[str, int]

class InterviewSession:
    """Manages an interview session with questions, responses, and metadata"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.status = InterviewStatus.PENDING
        self.interview_type = "general"
        self.user_data: Optional[UserData] = None
        
        # Interview content
        self.questions: List[QuestionData] = []
        self.user_responses: List[ResponseData] = []
        self.current_question = 0
        self.total_questions = 5
        
        # Timing
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration = 0
        
        # Metadata
        self.metadata = {
            "score": 0,
            "scoredResponses": 0,
            "scoringBreakdown": [],
            "lastActivity": datetime.now(),
            "clientIp": None,
            "userAgent": None
        }
        
        # Final results
        self.final_feedback: Optional[str] = None
        self.caregiver_evaluation: Optional[Dict] = None
    
    def start_interview(self, user_data: Dict, interview_type: str = "general"):
        """Start the interview with user data"""
        try:
            print(f"DEBUG: Starting interview with user_data: {user_data}")
            if isinstance(user_data, dict):
                self.user_data = UserData(**user_data)
                print(f"DEBUG: Created UserData object: {self.user_data}")
            else:
                self.user_data = user_data
            
            self.interview_type = interview_type
            self.status = InterviewStatus.ACTIVE
            self.start_time = datetime.now()
            self.metadata["lastActivity"] = datetime.now()
            
            # Set question count based on interview type
            if interview_type == "home_care":
                self.total_questions = 5
            else:
                self.total_questions = 5
                
            print(f"DEBUG: Interview started successfully with user: {self.user_data.firstName} {self.user_data.lastName}")
        except Exception as e:
            print(f"ERROR: Failed to start interview: {e}")
            print(f"ERROR: user_data received: {user_data}")
            # Create empty user data as fallback
            self.user_data = UserData()
            self.interview_type = interview_type
            self.status = InterviewStatus.ACTIVE
            self.start_time = datetime.now()
            self.metadata["lastActivity"] = datetime.now()
    
    def add_question(self, question: str) -> int:
        """Add a question to the session"""
        question_number = len(self.questions) + 1
        question_data = QuestionData(
            question=question,
            questionNumber=question_number
        )
        self.questions.append(question_data)
        self.metadata["lastActivity"] = datetime.now()
        return question_number
    
    def add_user_response(self, response: str, question_number: int, audio_path: Optional[str] = None) -> bool:
        """Add a user response"""
        if question_number <= 0 or question_number > len(self.questions):
            return False
        
        response_data = ResponseData(
            response=response,
            questionNumber=question_number,
            audioPath=audio_path
        )
        
        # Update existing response or add new one
        existing_idx = next(
            (i for i, r in enumerate(self.user_responses) 
             if r.questionNumber == question_number), 
            None
        )
        
        if existing_idx is not None:
            self.user_responses[existing_idx] = response_data
        else:
            self.user_responses.append(response_data)
        
        self.current_question = max(self.current_question, question_number)
        self.metadata["lastActivity"] = datetime.now()
        return True
    
    def add_analysis(self, analysis: str, question_number: int):
        """Add analysis for a response"""
        for response in self.user_responses:
            if response.questionNumber == question_number:
                response.analysis = analysis
                break
        self.metadata["lastActivity"] = datetime.now()
    
    def get_question(self, question_number: int) -> Optional[str]:
        """Get question by number"""
        for question in self.questions:
            if question.questionNumber == question_number:
                return question.question
        return None
    
    def get_current_question(self) -> Optional[str]:
        """Get current question"""
        if self.current_question > 0 and self.current_question <= len(self.questions):
            return self.questions[self.current_question - 1].question
        return None
    
    def get_user_response(self, question_number: int) -> Optional[str]:
        """Get user response by question number"""
        for response in self.user_responses:
            if response.questionNumber == question_number:
                return response.response
        return None
    
    def get_all_responses(self) -> List[str]:
        """Get all user responses"""
        return [r.response for r in sorted(self.user_responses, key=lambda x: x.questionNumber)]
    
    def get_all_questions(self) -> List[str]:
        """Get all questions"""
        return [q.question for q in sorted(self.questions, key=lambda x: x.questionNumber)]
    
    def get_progress(self) -> Dict:
        """Get interview progress"""
        return {
            "currentQuestion": self.current_question,
            "totalQuestions": self.total_questions,
            "questionsAnswered": len(self.user_responses),
            "percentComplete": (len(self.user_responses) / self.total_questions) * 100
        }
    
    def complete_interview(self, final_feedback: Optional[str] = None):
        """Mark interview as completed"""
        self.status = InterviewStatus.COMPLETED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        self.final_feedback = final_feedback
        self.metadata["lastActivity"] = datetime.now()
    
    def get_summary(self) -> Dict:
        """Get interview summary"""
        return {
            "sessionId": self.session_id,
            "status": self.status.value,
            "interviewType": self.interview_type,
            "userData": self.user_data.__dict__ if self.user_data else None,
            "progress": self.get_progress(),
            "startTime": self.start_time.isoformat() if self.start_time else None,
            "endTime": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "questionsCount": len(self.questions),
            "responsesCount": len(self.user_responses),
            "score": self.metadata.get("score", 0),
            "finalFeedback": self.final_feedback,
            "caregiverEvaluation": self.caregiver_evaluation,
            "scoringBreakdown": self.metadata.get("scoringBreakdown", [])
        }
    
    def get_full_transcript(self) -> List[Dict]:
        """Get full interview transcript"""
        transcript = []
        
        # Sort questions and responses by number
        questions_dict = {q.questionNumber: q for q in self.questions}
        responses_dict = {r.questionNumber: r for r in self.user_responses}
        
        max_question = max(len(self.questions), len(self.user_responses))
        
        for i in range(1, max_question + 1):
            question = questions_dict.get(i)
            response = responses_dict.get(i)
            
            if question or response:
                transcript.append({
                    "questionNumber": i,
                    "question": question.question if question else "",
                    "userResponse": response.response if response else "[No response recorded]",
                    "questionTimestamp": question.timestamp.isoformat() if question else None,
                    "responseTimestamp": response.timestamp.isoformat() if response else None,
                    "analysis": response.analysis if response else None,
                    "audioPath": response.audioPath if response else None
                })
        
        return transcript
    
    def update_last_activity(self):
        """Update last activity timestamp"""
        self.metadata["lastActivity"] = datetime.now()
    
    def is_active(self) -> bool:
        """Check if interview is active"""
        return self.status == InterviewStatus.ACTIVE
    
    def is_completed(self) -> bool:
        """Check if interview is completed"""
        return self.status == InterviewStatus.COMPLETED
    
    def can_proceed(self) -> bool:
        """Check if interview can proceed to next question"""
        return self.is_active() and self.current_question < self.total_questions
    
    def get_time_elapsed(self) -> float:
        """Get time elapsed since start"""
        if not self.start_time:
            return 0
        
        end_time = self.end_time or datetime.now()
        return (end_time - self.start_time).total_seconds()
    
    def get_formatted_duration(self) -> str:
        """Get formatted duration string"""
        elapsed = self.get_time_elapsed()
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        return f"{minutes}:{seconds:02d}"
    
    def set_error(self, error: str):
        """Set interview to error state"""
        self.status = InterviewStatus.ERROR
        self.metadata["error"] = error
        self.metadata["errorTime"] = datetime.now().isoformat()
        self.metadata["lastActivity"] = datetime.now()
    
    def reset(self):
        """Reset interview session"""
        self.status = InterviewStatus.PENDING
        self.questions.clear()
        self.user_responses.clear()
        self.current_question = 0
        self.start_time = None
        self.end_time = None
        self.duration = 0
        self.final_feedback = None
        self.caregiver_evaluation = None
        self.metadata = {
            "score": 0,
            "scoredResponses": 0,
            "scoringBreakdown": [],
            "lastActivity": datetime.now(),
            "clientIp": None,
            "userAgent": None
        }
    
    def export_data(self) -> Dict:
        """Export all session data"""
        return {
            "sessionId": self.session_id,
            "status": self.status.value,
            "interviewType": self.interview_type,
            "userData": self.user_data.__dict__ if self.user_data else None,
            "questions": [
                {
                    "question": q.question,
                    "questionNumber": q.questionNumber,
                    "timestamp": q.timestamp.isoformat()
                } for q in self.questions
            ],
            "responses": [
                {
                    "response": r.response,
                    "questionNumber": r.questionNumber,
                    "timestamp": r.timestamp.isoformat(),
                    "analysis": r.analysis
                } for r in self.user_responses
            ],
            "startTime": self.start_time.isoformat() if self.start_time else None,
            "endTime": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "metadata": {
                **self.metadata,
                "lastActivity": self.metadata["lastActivity"].isoformat()
            },
            "finalFeedback": self.final_feedback,
            "caregiverEvaluation": self.caregiver_evaluation
        }
    
    def cleanup(self):
        """Cleanup session resources"""
        # Clear large data structures
        self.questions.clear()
        self.user_responses.clear()
        self.final_feedback = None
        self.caregiver_evaluation = None
