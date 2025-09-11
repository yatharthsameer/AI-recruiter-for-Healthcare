"""
Gemini AI Service for Interview Question Generation and Response Analysis
Handles AI-powered interview logic using Google's Gemini API
"""
import os
import logging
from typing import List, Dict, Optional, Tuple
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for interacting with Google's Gemini AI"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        self.model = None
        self.initialized = False
        
        if self.api_key:
            self._initialize()
        else:
            logger.warning("GEMINI_API_KEY not set, using fallback mode")
    
    def _initialize(self):
        """Initialize the Gemini client"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self.initialized = True
            logger.info(f"✅ Gemini API initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini API: {e}")
            self.initialized = False
    
    async def generate_question(
        self, 
        interview_type: str = "general", 
        question_number: int = 0, 
        history: List[Dict] = None, 
        user_data: Dict = None
    ) -> str:
        """Generate interview question using Gemini AI"""
        try:
            if not self.initialized:
                return self._get_dynamic_followup_question(interview_type, question_number, history)
            
            prompt = self._build_question_prompt(interview_type, question_number, history, user_data)
            
            response = self.model.generate_content(prompt)
            question = response.text.strip()
            
            logger.info(f"Generated question {question_number + 1} for {interview_type} interview")
            return question
            
        except Exception as e:
            logger.error(f"Error generating question: {e}")
            return self._get_dynamic_followup_question(interview_type, question_number, history)
    
    async def analyze_response(
        self, 
        response: str, 
        question_number: int, 
        history: List[Dict] = None
    ) -> str:
        """Analyze candidate response using Gemini AI"""
        try:
            if not self.initialized:
                return self._get_fallback_analysis(response, question_number)
            
            prompt = self._build_analysis_prompt(response, question_number, history)
            
            result = self.model.generate_content(prompt)
            analysis = result.text.strip()
            
            logger.info(f"Analyzed response for question {question_number + 1}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing response: {e}")
            return self._get_fallback_analysis(response, question_number)
    
    async def generate_final_feedback(
        self, 
        responses: List[str], 
        interview_type: str
    ) -> str:
        """Generate final interview feedback"""
        try:
            if not self.initialized:
                return self._get_fallback_final_feedback(responses, interview_type)
            
            prompt = self._build_final_feedback_prompt(responses, interview_type)
            
            result = self.model.generate_content(prompt)
            feedback = result.text.strip()
            
            logger.info(f"Generated final feedback for {interview_type} interview")
            return feedback
            
        except Exception as e:
            logger.error(f"Error generating final feedback: {e}")
            return self._get_fallback_final_feedback(responses, interview_type)
    
    async def generate_transcript_summary(
        self, 
        transcript_text: str, 
        interview_type: str = "general", 
        user_data: Dict = None
    ) -> str:
        """Generate AI summary from full transcript"""
        try:
            if not self.initialized:
                # Simple fallback summary
                trimmed = (transcript_text or '')[:800]
                return f"Summary (fallback) for {interview_type}:\n{trimmed}\n..."
            
            # Enhanced caregiver-specific evaluation prompt
            if interview_type == 'home_care':
                prompt = self._build_caregiver_evaluation_prompt(transcript_text, user_data)
            else:
                prompt = self._build_general_summary_prompt(transcript_text, interview_type)
            
            result = self.model.generate_content(prompt)
            summary = result.text.strip()
            
            logger.info(f"Generated transcript summary for {interview_type} interview")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating transcript summary: {e}")
            return 'Unable to generate AI summary at this time. Please try again later.'
    
    def _build_question_prompt(
        self, 
        interview_type: str, 
        question_number: int, 
        history: List[Dict] = None, 
        user_data: Dict = None
    ) -> str:
        """Build prompt for question generation"""
        
        interview_types = {
            "general": "general behavioral interview",
            "technical": "technical or software engineering interview",
            "coding": "coding interview with live problem solving",
            "sales": "sales and business development interview",
            "leadership": "leadership and management interview",
            "customer_service": "customer service interview",
            "home_care": "home care / caregiver interview"
        }
        
        type_description = interview_types.get(interview_type, interview_types["general"])
        history_text = self._format_history(history or [])
        
        # Enhanced prompt for caregiver interviews
        if interview_type == 'home_care':
            candidate_context = ""
            if user_data:
                candidate_context = f"""
CANDIDATE BACKGROUND:
- Name: {user_data.get('firstName', '')} {user_data.get('lastName', '')}
- Position Applied: {user_data.get('position', '')}
- HHA Experience: {'Yes' if user_data.get('hhaExperience') else 'No'}
- CPR Certified: {'Yes' if user_data.get('cprCertified') else 'No'}
- Driver's License: {'Yes' if user_data.get('driversLicense') else 'No'}
- Reliable Transport: {'Yes' if user_data.get('reliableTransport') else 'No'}
- Availability: {', '.join(user_data.get('availability', []))}
- Preferred Hours/Week: {user_data.get('weeklyHours', 'Not specified')}
- Location Preference: {user_data.get('locationPref', 'Not specified')}

Use this information to personalize questions and probe deeper into relevant areas.
"""
            
            return f"""
You are an expert interviewer conducting a caregiver interview for FirstLight Home Care. 
Keep questions SHORT and CONVERSATIONAL - maximum 2 sentences.
{candidate_context}
CAREGIVER INTERVIEW FOCUS:
- Assess empathy, patience, and problem-solving skills
- Ask about specific caregiving experiences and challenging situations
- Evaluate communication skills and emotional intelligence
- Focus on safety awareness and following protocols
- Assess commitment and stress management

QUESTION GUIDELINES:
- Keep questions under 30 words
- Ask for specific examples and stories
- Avoid yes/no questions
- Be warm but professional
- Build on previous responses naturally
- Encourage concise but detailed responses (aim for 1-2 minute answers)
- Use candidate's background to personalize questions when relevant

This is question {question_number + 1} of 5 (targeting ~10 minute interview). Focus on these areas by question:
Question 1: Experience and motivation for caregiving (consider their HHA experience)
Question 2: Handling difficult clients or challenging situations
Question 3: Situational scenarios (medication compliance, care refusal, etc.)
Question 4: Skills assessment and self-awareness (consider certifications)
Question 5: Commitment and what motivates them in tough times (consider availability/hours)

SAMPLE QUESTION STYLES:
- "Tell me about a time when you cared for someone who was difficult or resistant..."
- "What would you do if a client refused to take their medication after you reminded them?"
- "Describe your experience caring for others - what was most challenging and most meaningful?"
- "What caregiving skill are you strongest in, and what area would you like to develop?"

Conversation so far:
{history_text}

Generate a SHORT, focused caregiver question (under 30 words):"""
        
        # General interview prompt
        return f"""
You are an expert interviewer conducting a friendly and natural conversation for a {type_description}. 
Keep your questions SHORT and CONCISE - maximum 2 sentences.

IMPORTANT: 
- Keep questions under 35 words when possible
- Be direct and clear
- Avoid long explanations or context
- Ask one focused question at a time

Start the first question by greeting the candidate briefly, then ask a simple opening question.

For follow-up questions, use brief transitions like "Got it" or "Thanks" then ask the next question directly.

Ask open-ended questions that invite specific examples, not yes/no answers.
This is question {question_number + 1} of 5 in the interview.

Conversation so far:
{history_text}

Generate a SHORT, focused question (under 25 words):"""
    
    def _build_analysis_prompt(
        self, 
        response: str, 
        question_number: int, 
        history: List[Dict] = None
    ) -> str:
        """Build prompt for response analysis"""
        history_text = self._format_history(history or [])
        
        return f"""
You are an expert interview coach. Analyze the candidate's response to question {question_number + 1}. 

Candidate's response: 
{response}

Conversation history: 
{history_text}

Provide a single human sounding paragraph that includes:
- A quick assessment of their answer
- The strengths they showed
- Areas they could improve
- A short, encouraging tip for future interviews"""
    
    def _build_final_feedback_prompt(self, responses: List[str], interview_type: str) -> str:
        """Build prompt for final feedback"""
        response_text = "\n".join([f"Q{i + 1}: {r}" for i, r in enumerate(responses)])
        
        return f"""
You are a helpful interview coach giving final feedback after a {interview_type} interview.

Here are the candidate's responses:
{response_text}

Provide feedback in 3 or 4 short paragraphs that cover:
1. Overall performance
2. Key strengths
3. Areas for improvement
4. Specific actionable advice
5. Close on a positive and encouraging note"""
    
    def _build_caregiver_evaluation_prompt(self, transcript_text: str, user_data: Dict = None) -> str:
        """Build caregiver-specific evaluation prompt"""
        candidate_context = ""
        if user_data:
            candidate_context = f"""
CANDIDATE BACKGROUND:
- Name: {user_data.get('firstName', '')} {user_data.get('lastName', '')}
- Position Applied: {user_data.get('position', '')}
- HHA Experience: {'Yes' if user_data.get('hhaExperience') else 'No'}
- CPR Certified: {'Yes' if user_data.get('cprCertified') else 'No'}
- Driver's License: {'Yes' if user_data.get('driversLicense') else 'No'}
- Reliable Transport: {'Yes' if user_data.get('reliableTransport') else 'No'}
- Availability: {', '.join(user_data.get('availability', []))}
- Preferred Hours/Week: {user_data.get('weeklyHours', 'Not specified')}
- Location Preference: {user_data.get('locationPref', 'Not specified')}

Consider this background when evaluating their responses and making recommendations.
"""
        
        return f"""You are an expert caregiver hiring manager for FirstLight Home Care. Analyze this interview transcript and provide a comprehensive evaluation.
{candidate_context}
CAREGIVER EVALUATION CRITERIA:
1. EMPATHY & COMPASSION - Ability to understand and connect with clients emotionally
2. SAFETY AWARENESS - Knowledge of protocols, emergency procedures, and risk management
3. COMMUNICATION SKILLS - Clear, respectful, and effective interaction abilities
4. PROBLEM-SOLVING - Ability to handle difficult situations and make sound decisions
5. EXPERIENCE & COMMITMENT - Relevant background and dedication to caregiving

EVALUATION INSTRUCTIONS:
- Assess each criterion based on the candidate's responses
- Look for specific examples, emotional intelligence, and professional maturity
- Consider their approach to difficult situations and client interactions
- Evaluate their understanding of caregiver responsibilities
- Factor in their background qualifications and experience level

REQUIRED SECTIONS:
1) EXECUTIVE SUMMARY (2-3 sentences overall assessment)
2) COMPETENCY ANALYSIS
   - Empathy & Compassion: [Score/10] - [Brief assessment]
   - Safety Awareness: [Score/10] - [Brief assessment]  
   - Communication Skills: [Score/10] - [Brief assessment]
   - Problem-Solving: [Score/10] - [Brief assessment]
   - Experience & Commitment: [Score/10] - [Brief assessment]
3) KEY STRENGTHS (Top 2-3 observed strengths, including background qualifications)
4) DEVELOPMENT AREAS (Areas needing improvement, considering current qualifications)
5) BEHAVIORAL INSIGHTS (Professional maturity, emotional stability, cultural fit)
6) HIRING RECOMMENDATION
   - Recommendation: [Highly Recommended/Recommended/Consider with Training/Not Recommended]
   - Confidence Level: [High/Medium/Low]
   - Reasoning: [2-3 sentences considering both interview performance and background]
7) NEXT STEPS (Specific actions recommended based on their profile)

TRANSCRIPT:
{transcript_text}

Provide detailed, actionable feedback suitable for hiring decisions."""
    
    def _build_general_summary_prompt(self, transcript_text: str, interview_type: str) -> str:
        """Build general interview summary prompt"""
        return f"""You are an expert hiring interviewer. Read the FULL interview transcript below and produce a concise, professional candidate report suitable for a PDF.

Role/Domain: {interview_type}

INSTRUCTIONS:
- Be objective, use a warm but concise tone.
- Structure into clear sections with short paragraphs and bullet points where appropriate:
  1) Overview
  2) Strengths
  3) Areas for Improvement
  4) Communication & Soft Skills
  5) Role-specific Aptitude
  6) Final Recommendation
- Provide a final numeric score from 0 to 100 at the end as: "Score: NN/100".

TRANSCRIPT START
{transcript_text}
TRANSCRIPT END"""
    
    def _get_dynamic_followup_question(
        self, 
        interview_type: str, 
        question_number: int, 
        history: List[Dict] = None
    ) -> str:
        """Get fallback question when AI is unavailable"""
        
        # Caregiver-specific fallback questions
        if interview_type == "home_care":
            if not history:
                return "Hi! Tell me about your experience caring for others - whether professional, personal, or volunteer work."
            
            caregiver_prompts = [
                "Describe a time when you cared for someone who was difficult or resistant. How did you handle it?",
                "What would you do if a client refused to take their prescribed medication?",
                "What caregiving skill are you strongest in, and what area would you like to develop?",
                "What draws you to caregiving work, and what keeps you motivated during tough days?",
                "Tell me about a time when you had to make a quick decision while caring for someone."
            ]
            
            return caregiver_prompts[question_number % len(caregiver_prompts)]
        
        # Default fallback for other interview types
        if not history:
            if interview_type == "coding":
                return "Hi! Tell me about a recent coding challenge you solved."
            return "Hi! Please introduce yourself and share a recent achievement."
        
        prompts = [
            "Can you walk me through your approach?",
            "What was the outcome? Any specific results?",
            "How would you improve it next time?",
            "What challenges did you face?",
            "Tell me about your decision-making process."
        ]
        
        if interview_type == "coding":
            prompts.extend([
                "What's the time complexity of your solution?",
                "How would you handle larger inputs?"
            ])
        
        return prompts[question_number % len(prompts)]
    
    def _get_fallback_analysis(self, response: str, question_number: int) -> str:
        """Get fallback analysis when AI is unavailable"""
        generic_comments = [
            "Good response, you communicated your thoughts clearly.",
            "Nice answer, you could add more concrete results or metrics.",
            "Well done, your answer shows clear problem solving skills.",
            "Solid response, consider explaining the impact more deeply.",
            "Great effort, you might expand by adding specific examples."
        ]
        
        base = generic_comments[question_number % len(generic_comments)]
        hint = " Try giving more details with concrete examples." if len(response) < 80 else ""
        return base + hint
    
    def _get_fallback_final_feedback(self, responses: List[str], interview_type: str) -> str:
        """Get fallback final feedback when AI is unavailable"""
        return f"""
Overall you did well in this {interview_type} interview. You showed clear communication and thoughtful answers. 

Your strengths include presenting ideas logically and giving relevant experiences. 
You seem well prepared and engaged with the questions. 

For future interviews, try to add more results, measurable achievements, or detailed examples to make your answers more memorable. 

You are on the right track. Keep practicing and you will only get stronger and more confident."""
    
    def _format_history(self, history: List[Dict]) -> str:
        """Format conversation history for prompts"""
        if not history:
            return "(no prior conversation)"
        
        formatted = []
        for i, item in enumerate(history):
            question = item.get('question', '')
            response = item.get('response', '')
            formatted.append(f"Q{i + 1}: {question}\nA{i + 1}: {response}")
        
        return "\n".join(formatted)
    
    def health_check(self) -> Dict:
        """Check Gemini service health"""
        try:
            if not self.api_key:
                return {
                    "status": "warning",
                    "message": "GEMINI_API_KEY not configured"
                }
            
            if not self.initialized:
                return {
                    "status": "error", 
                    "message": "Gemini API not initialized"
                }
            
            # Test with a simple prompt
            test_response = self.model.generate_content("Hello, just testing connection")
            test_response.text  # This will raise an exception if there's an issue
            
            return {
                "status": "healthy",
                "message": "Gemini API connection successful",
                "model": self.model_name
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Gemini API connection failed: {str(e)}"
            }

# Global instance
gemini_service = GeminiService()
