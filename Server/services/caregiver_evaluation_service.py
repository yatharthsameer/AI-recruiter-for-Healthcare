"""
Simple Caregiver Evaluation Service
Evaluates candidates on 5 dimensions using clean Gemini AI analysis
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from .gemini_service import gemini_service

logger = logging.getLogger(__name__)


class CaregiverEvaluationService:
    """Simple service for evaluating caregiver interview performance"""

    def __init__(self):
        self.evaluation_dimensions = [
            "Experience & Skills",
            "Motivation",
            "Punctuality",
            "Compassion and Empathy",
            "Communication",
        ]

    async def evaluate_candidate(self, interview_data: Dict) -> Dict:
        """
        Evaluate caregiver candidate based on interview transcript

        Args:
            interview_data: Dictionary containing:
                - transcript: Full interview transcript
                - userData: Candidate information
                - sessionId: Interview session ID

        Returns:
            Evaluation with 5-dimension scores (0-10)
        """
        try:
            transcript = interview_data.get("transcript", "")
            user_data = interview_data.get('userData', {})
            session_id = interview_data.get("sessionId", "")

            logger.info(f"Starting evaluation for session {session_id}")

            # Get evaluation scores from Gemini
            scores = await self._get_gemini_evaluation(transcript, user_data)

            # Create evaluation result
            evaluation = {
                "evaluationId": f"eval_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "sessionId": session_id,
                "candidateInfo": user_data,
                "transcript": transcript,
                "scores": scores,
                "overallScore": round(sum(scores.values()) / len(scores), 1),
                "evaluationType": "text-based",
            }

            logger.info(
                f"Evaluation completed for session {session_id} - Overall Score: {evaluation['overallScore']}"
            )
            return evaluation

        except Exception as e:
            logger.error(f"Error in caregiver evaluation: {e}")
            return self._get_fallback_evaluation(interview_data)

    async def _get_gemini_evaluation(
        self, transcript: str, user_data: Dict
    ) -> Dict[str, float]:
        """Get evaluation scores from Gemini AI"""

        try:
            # Use the new clean Gemini service
            response = await gemini_service.generate_evaluation_scores(
                transcript, user_data
            )
            scores = self._parse_gemini_scores(response)
            return scores

        except Exception as e:
            logger.error(f"Error getting Gemini evaluation: {e}")
            # Return default scores if Gemini fails
            return {dimension: 5.0 for dimension in self.evaluation_dimensions}

    def _parse_gemini_scores(self, response: str) -> Dict[str, float]:
        """Parse scores from Gemini response"""

        try:
            # Clean the response to extract JSON
            response = response.strip()

            # Find JSON object in response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON object found in response")

            json_str = response[start_idx:end_idx]
            scores_dict = json.loads(json_str)

            # Validate and clean scores
            validated_scores = {}
            for dimension in self.evaluation_dimensions:
                if dimension in scores_dict:
                    score = float(scores_dict[dimension])
                    # Ensure score is between 0 and 10
                    validated_scores[dimension] = max(0.0, min(10.0, score))
                else:
                    logger.warning(f"Missing score for dimension: {dimension}")
                    validated_scores[dimension] = 5.0  # Default score

            return validated_scores

        except Exception as e:
            logger.error(f"Error parsing Gemini scores: {e}")
            logger.error(f"Response was: {response}")
            # Return default scores
            return {dimension: 5.0 for dimension in self.evaluation_dimensions}

    def _get_fallback_evaluation(self, interview_data: Dict) -> Dict:
        """Return fallback evaluation when processing fails"""

        session_id = interview_data.get("sessionId", "unknown")
        user_data = interview_data.get("userData", {})
        transcript = interview_data.get("transcript", "")

        return {
            "evaluationId": f"fallback_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "sessionId": session_id,
            "candidateInfo": user_data,
            "transcript": transcript,
            "scores": {dimension: 5.0 for dimension in self.evaluation_dimensions},
            "overallScore": 5.0,
            "evaluationType": "fallback",
            "error": "Automated evaluation failed - default scores assigned",
        }


# Global instance
caregiver_evaluation_service = CaregiverEvaluationService()
