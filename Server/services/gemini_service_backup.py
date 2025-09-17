"""
Clean Gemini AI Service for Natural Caregiver Interviews
Simple text generation for conversational interviews
"""

import os
import logging
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
logger = logging.getLogger(__name__)


class GeminiService:
    """Simple service for natural conversation interviews using Gemini AI"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.model = None
        self.initialized = False

        if self.api_key:
            self._initialize()
        else:
            logger.warning("GEMINI_API_KEY not set, running in fallback mode")

    def _initialize(self):
        """Initialize Gemini client for natural conversation"""
        try:
            genai.configure(api_key=self.api_key)

            # Simple system instruction for natural conversation
            system_instruction = """You are a warm, professional interviewer conducting caregiver interviews. 
            
Your role:
- Be conversational, friendly, and professional
- Ask SHORT, simple questions (1-2 sentences maximum)
- Show genuine interest in responses
- Handle candidate questions gracefully
- Keep responses brief and focused
- Never output JSON, metadata, or structured data
- Only respond with natural human speech

CRITICAL: Keep ALL responses SHORT. Never ask multiple questions at once. One simple question or comment at a time.
            
Remember: You are having a real conversation, not generating structured data."""

            self.model = genai.GenerativeModel(
                self.model_name, system_instruction=system_instruction
            )
            self.initialized = True
            logger.info(
                f"✅ Gemini initialized for natural conversation ({self.model_name})"
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {e}")
            self.initialized = False

    async def generate_simple_response(self, prompt: str) -> str:
        """Generate a simple text response for natural conversation"""
        try:
            if not self.initialized:
                return "I'm sorry, I'm having technical difficulties. Could you please try again?"

            # Generate simple text response
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_output_tokens": 50,  # Force very short responses
                },
            )

            if response and response.text:
                return response.text.strip()
            else:
                return "I'm sorry, could you please repeat that?"

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm sorry, I'm having technical difficulties. Could you please try again?"

    async def start_natural_interview(
        self, candidate_name: str, interview_type: str, user_data: Dict
    ) -> str:
        """Start a natural, conversational interview"""

        # Get the first standardized question to start with
        from .topic_coverage_tracker import topic_coverage_tracker

        required_questions = (
            topic_coverage_tracker.get_required_questions_for_missing_topics()
        )
        first_question = (
            required_questions[0]
            if required_questions
            else "Could you tell me a bit about yourself and what brings you to caregiving?"
        )

        prompt = f"""Start a caregiver interview with {candidate_name}.

Be warm and welcoming, then ask this specific question naturally: "{first_question}"

CRITICAL REQUIREMENTS:
- Keep it SHORT (1-2 sentences maximum)
- Start with a brief greeting
- Ask the question in a natural, conversational way
- Be friendly but brief
- Don't mention it's a "required question"

Respond ONLY with what you would say as the interviewer. No JSON, no metadata, just natural speech."""

        try:
            response = await self.generate_simple_response(prompt)
            return response
        except Exception as e:
            logger.error(f"Error starting natural interview: {e}")
            # Simple fallback with first standardized question
            name_part = f"Hi {candidate_name}, " if candidate_name else "Hi there, "
            return f"{name_part}thanks for taking the time to speak with me today! {first_question}"

    async def continue_natural_interview(
        self,
        conversation_history: List[Dict],
        coverage_summary: Dict,
        interview_type: str,
        user_data: Dict,
    ) -> str:
        """Continue the natural interview conversation"""

        # Get recent conversation context
        recent_history = (
            conversation_history[-4:]
            if len(conversation_history) > 4
            else conversation_history
        )

        # Format conversation for context
        conversation_text = ""
        for exchange in recent_history:
            role = "Interviewer" if exchange["role"] == "interviewer" else "Candidate"
            conversation_text += f"{role}: {exchange['content']}\n"

        # Prepare coverage information for guidance
        covered_topics = [topic["name"] for topic in coverage_summary["covered_topics"]]
        missing_topics = [topic["name"] for topic in coverage_summary["missing_topics"]]
        completion_pct = coverage_summary["completion_percentage"]

        # Get required questions for missing topics
        from .topic_coverage_tracker import topic_coverage_tracker

        required_questions = (
            topic_coverage_tracker.get_required_questions_for_missing_topics()
        )

        # Build the prompt with required questions
        required_questions_text = ""
        if required_questions:
            required_questions_text = "\nREQUIRED QUESTIONS (choose one that fits naturally in conversation):\n"
            for i, question in enumerate(
                required_questions[:3], 1
            ):  # Limit to 3 to keep prompt manageable
                required_questions_text += f"{i}. {question}\n"

        prompt = f"""Continue this caregiver interview conversation naturally.

Recent conversation:
{conversation_text}
{required_questions_text}
Interview progress (for your guidance only - don't mention this):
- Covered: {', '.join(covered_topics) if covered_topics else 'None yet'}
- Still need: {', '.join(missing_topics) if missing_topics else 'All covered'}
- Progress: {completion_pct:.0f}%

CRITICAL REQUIREMENTS:
- Keep response SHORT (1-2 sentences maximum)
- Ask only ONE simple question or make ONE brief comment
- If there are required questions above, ask ONE of them in a natural, conversational way
- Don't mention it's a "required question" - make it feel natural
- Don't overwhelm with multiple questions
- Be natural but concise

Respond ONLY with what you would say as the interviewer. No JSON, no metadata, just brief natural speech."""

        try:
            response = await self.generate_simple_response(prompt)
            return response
        except Exception as e:
            logger.error(f"Error continuing natural interview: {e}")
            return "That's interesting. Could you tell me more about that experience?"

    def health_check(self) -> Dict[str, Any]:
        """Simple health check"""
        if not self.api_key:
            return {"status": "warning", "message": "GEMINI_API_KEY not configured"}
        if not self.initialized:
            return {"status": "error", "message": "Gemini not initialized"}

        try:
            # Simple test
            test_response = self.model.generate_content("Say 'OK'")
            if test_response and test_response.text and "OK" in test_response.text:
                return {
                    "status": "healthy",
                    "model": self.model_name,
                }
            return {"status": "error", "message": "Unexpected health response"}
        except Exception as e:
            return {"status": "error", "message": f"Health call failed: {e}"}

    async def generate_evaluation_scores(self, transcript: str, user_data: Dict) -> str:
        """Generate evaluation scores for interview transcript"""

        candidate_info = f"""
Candidate: {user_data.get('firstName', '')} {user_data.get('lastName', '')}
Experience: {'Yes' if user_data.get('caregivingExperience') else 'No'}
Availability: {', '.join(user_data.get('availability', []))}
Weekly Hours: {user_data.get('weeklyHours', 0)}
"""

        prompt = f"""You are evaluating a caregiver interview. Analyze the transcript and provide numerical scores.

{candidate_info}

Interview Transcript:
{transcript}

Rate on these 5 dimensions (0-10 scale):
1. Experience & Skills: Relevant experience, technical abilities, training
2. Motivation: Genuine interest, commitment, understanding of role  
3. Punctuality: Reliability, time management (infer from responses)
4. Compassion and Empathy: Care for others, emotional intelligence
5. Communication: Clarity, listening skills, professionalism

CRITICAL: Respond ONLY with this exact JSON format, no other text:
{{
    "Experience & Skills": 7.5,
    "Motivation": 8.0,
    "Punctuality": 6.5,
    "Compassion and Empathy": 9.0,
    "Communication": 7.0
}}"""

        try:
            # Use direct model call for structured output
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,  # Low temperature for consistent JSON
                    "max_output_tokens": 150,
                },
            )

            if response and response.text:
                return response.text.strip()
            else:
                return '{"Experience & Skills": 5.0, "Motivation": 5.0, "Punctuality": 5.0, "Compassion and Empathy": 5.0, "Communication": 5.0}'

        except Exception as e:
            logger.error(f"Error generating evaluation: {e}")
            return '{"Experience & Skills": 5.0, "Motivation": 5.0, "Punctuality": 5.0, "Compassion and Empathy": 5.0, "Communication": 5.0}'

    async def generate_transcript_summary(
        self, transcript: str, interview_type: str, user_data: Optional[Dict] = None
    ) -> str:
        """Generate a summary and feedback for the interview transcript"""

        candidate_name = ""
        if user_data:
            candidate_name = f"{user_data.get('firstName', '')} {user_data.get('lastName', '')}".strip()

        prompt = f"""Provide a brief, encouraging summary of this caregiver interview.

Candidate: {candidate_name or 'Candidate'}
Interview Type: {interview_type}

Interview Transcript:
{transcript}

Write a warm, professional summary that:
1. Acknowledges their participation
2. Highlights 2-3 positive aspects from their responses
3. Provides encouraging feedback
4. Keeps it brief (2-3 sentences)

Be conversational and supportive, as if speaking directly to the candidate."""

        try:
            response = await self.generate_simple_response(prompt)
            return response
        except Exception as e:
            logger.error(f"Error generating transcript summary: {e}")
            return f"Thank you for completing the interview{f', {candidate_name}' if candidate_name else ''}! We appreciate the time you took to share your experiences and interest in caregiving. We'll be in touch soon regarding next steps."


# Global instance
gemini_service = GeminiService()
