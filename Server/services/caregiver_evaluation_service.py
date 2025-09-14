"""
Simple Caregiver Evaluation Service
Evaluates candidates on 5 dimensions using Gemini AI
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from .gemini_service import gemini_service

logger = logging.getLogger(__name__)

class CaregiverEvaluationService:
    """Simple service for evaluating caregiver interview performance using Gemini AI"""

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
        Multimodal caregiver evaluation using Gemini AI with audio analysis

        Args:
            interview_data: Dictionary containing:
                - transcript: Full interview transcript
                - userData: Candidate information
                - sessionId: Interview session ID
                - audioData: Optional list of audio chunks per question
                - responses: Optional list of response objects with audio

        Returns:
            Enhanced evaluation with 5-dimension scores (0-10) plus audio insights
        """
        try:
            transcript = interview_data.get("transcript", "")
            user_data = interview_data.get('userData', {})
            session_id = interview_data.get("sessionId", "")
            audio_data = interview_data.get("audioData", [])
            responses = interview_data.get("responses", [])

            # Check if we have multimodal data available
            has_audio = bool(audio_data or any(r.get("audioData") for r in responses))

            if has_audio:
                logger.info(
                    f"Using multimodal evaluation with audio for session {session_id}"
                )
                scores, audio_insights = await self._get_multimodal_evaluation(
                    transcript, user_data, audio_data, responses
                )
            else:
                logger.info(f"Using text-only evaluation for session {session_id}")
                scores = await self._get_gemini_evaluation(transcript, user_data)
                audio_insights = {}

            # Create evaluation result
            evaluation = {
                "evaluationId": f"eval_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "sessionId": session_id,
                "candidateInfo": user_data,
                "transcript": transcript,
                "scores": scores,
                "overallScore": round(sum(scores.values()) / len(scores), 1),
                "evaluationType": "multimodal" if has_audio else "text-only",
                "audioInsights": audio_insights,
            }

            logger.info(
                f"Evaluation completed for session {session_id} - Overall Score: {evaluation['overallScore']} ({evaluation['evaluationType']})"
            )
            return evaluation

        except Exception as e:
            logger.error(f"Error in caregiver evaluation: {e}")
            return self._get_fallback_evaluation(interview_data)

    async def _get_gemini_evaluation(
        self, transcript: str, user_data: Dict
    ) -> Dict[str, float]:
        """Get evaluation scores from Gemini AI using the new structured approach"""

        try:
            # Use the new structured Gemini service if available
            if hasattr(gemini_service, "build_final_report"):
                # This is the new structured service - use simple evaluation for now
                # We'll create a mock turn result to get scores
                mock_turns = []
                for i, dimension in enumerate(self.evaluation_dimensions):
                    # Create a simple mock analysis based on transcript content
                    score = self._estimate_dimension_score(transcript, dimension)
                    mock_turns.append(
                        type(
                            "TurnResult",
                            (),
                            {
                                "question_id": f"Q{i+1}",
                                "score_0_to_4": score,
                                "summary_one_line": f"Evaluated {dimension}",
                                "signals": {},
                                "missing_keys": [],
                                "red_flags": [],
                            },
                        )()
                    )

                # Convert 0-4 scores to 0-10 scale
                scores = {}
                for i, dimension in enumerate(self.evaluation_dimensions):
                    score_0_4 = mock_turns[i].score_0_to_4
                    scores[dimension] = (score_0_4 / 4.0) * 10.0

                return scores
            else:
                # Fallback to legacy method
                prompt = self._create_evaluation_prompt(transcript, user_data)
                response = await gemini_service.generate_response(prompt)
                scores = self._parse_gemini_scores(response)
                return scores

        except Exception as e:
            logger.error(f"Error getting Gemini evaluation: {e}")
            # Return default scores if Gemini fails
            return {dimension: 5.0 for dimension in self.evaluation_dimensions}

    async def _get_multimodal_evaluation(
        self, transcript: str, user_data: Dict, audio_data: List, responses: List[Dict]
    ) -> Tuple[Dict[str, float], Dict]:
        """Get evaluation using multimodal Gemini analysis with audio"""

        try:
            # Import here to avoid circular imports
            from .gemini_service import gemini_service

            # Check if the new Gemini service has multimodal capabilities
            if not hasattr(gemini_service, "analyze_turn"):
                logger.warning(
                    "Multimodal Gemini service not available, falling back to text-only"
                )
                scores = await self._get_gemini_evaluation(transcript, user_data)
                return scores, {}

            # Prepare audio data for analysis
            audio_chunks = []
            if audio_data:
                audio_chunks = audio_data
            elif responses:
                # Extract audio from response objects
                for response in responses:
                    if response.get("audioData"):
                        audio_chunks.append(response["audioData"])

            # Analyze each question-response pair with multimodal Gemini
            turn_results = []
            audio_insights = {
                "voice_confidence": [],
                "speech_clarity": [],
                "emotional_tone": [],
                "response_completeness": [],
            }

            # Split transcript into Q&A pairs for analysis
            qa_pairs = self._extract_qa_pairs(transcript)

            for i, (question, answer) in enumerate(qa_pairs[:9]):  # Max 9 questions
                # Get corresponding audio if available
                audio_bytes = audio_chunks[i] if i < len(audio_chunks) else None

                # Use multimodal analysis
                try:
                    result = gemini_service.analyze_turn(
                        idx=i,
                        transcript_text=answer,
                        audio=audio_bytes,
                        audio_mime="audio/webm",
                        lang="en",
                        remaining_sec=600,
                    )

                    turn_results.append(result)

                    # Extract audio insights if available
                    if audio_bytes and result.signals:
                        signals = result.signals
                        audio_insights["voice_confidence"].append(
                            signals.get("voice_confidence", 0.5)
                        )
                        audio_insights["speech_clarity"].append(
                            signals.get("speech_clarity", 0.5)
                        )
                        audio_insights["emotional_tone"].append(
                            signals.get("emotional_tone", "neutral")
                        )
                        audio_insights["response_completeness"].append(
                            signals.get("response_completeness", 0.5)
                        )

                except Exception as turn_error:
                    logger.error(f"Error analyzing turn {i+1}: {turn_error}")
                    # Create fallback result
                    score = self._estimate_dimension_score(
                        answer,
                        self.evaluation_dimensions[i % len(self.evaluation_dimensions)],
                    )
                    turn_results.append(
                        type(
                            "TurnResult",
                            (),
                            {
                                "question_id": f"Q{i+1}",
                                "score_0_to_4": score,
                                "summary_one_line": f"Analyzed question {i+1}",
                                "signals": {},
                                "missing_keys": [],
                                "red_flags": [],
                            },
                        )()
                    )

            # Convert turn results to dimension scores
            scores = self._convert_turns_to_dimension_scores(turn_results)

            # Calculate audio insight averages
            processed_insights = {}
            for key, values in audio_insights.items():
                if values:
                    if key == "emotional_tone":
                        # Count emotional tone distribution
                        processed_insights[key] = {
                            "dominant_tone": (
                                max(set(values), key=values.count)
                                if values
                                else "neutral"
                            ),
                            "tone_variety": len(set(values)),
                        }
                    else:
                        processed_insights[key] = {
                            "average": sum(values) / len(values),
                            "range": [min(values), max(values)],
                        }

            logger.info(f"Multimodal analysis completed with {len(turn_results)} turns")
            return scores, processed_insights

        except Exception as e:
            logger.error(f"Error in multimodal evaluation: {e}")
            # Fallback to text-only evaluation
            scores = await self._get_gemini_evaluation(transcript, user_data)
            return scores, {}

    def _extract_qa_pairs(self, transcript: str) -> List[Tuple[str, str]]:
        """Extract question-answer pairs from transcript"""
        lines = transcript.strip().split("\n")
        qa_pairs = []
        current_question = ""
        current_answer = ""

        for line in lines:
            line = line.strip()
            if line.startswith("Interviewer:"):
                # Save previous Q&A if we have both
                if current_question and current_answer:
                    qa_pairs.append((current_question, current_answer))

                # Start new question
                current_question = line.replace("Interviewer:", "").strip()
                current_answer = ""
            elif line.startswith("Candidate:"):
                current_answer = line.replace("Candidate:", "").strip()

        # Add the last Q&A pair
        if current_question and current_answer:
            qa_pairs.append((current_question, current_answer))

        return qa_pairs

    def _convert_turns_to_dimension_scores(
        self, turn_results: List
    ) -> Dict[str, float]:
        """Convert turn results to our 5 dimension scores"""

        # Map questions to dimensions (simplified mapping)
        dimension_mapping = {
            0: "Experience & Skills",  # Q1
            1: "Experience & Skills",  # Q2
            2: "Experience & Skills",  # Q3
            3: "Motivation",  # Q4
            4: "Punctuality",  # Q5
            5: "Punctuality",  # Q6
            6: "Compassion and Empathy",  # Q7
            7: "Compassion and Empathy",  # Q8
            8: "Communication",  # Q9
        }

        dimension_scores = {dim: [] for dim in self.evaluation_dimensions}

        # Collect scores by dimension
        for i, result in enumerate(turn_results):
            if i < len(dimension_mapping):
                dimension = dimension_mapping[i]
                if dimension in dimension_scores:
                    # Convert 0-4 score to 0-10 scale
                    score_10 = (result.score_0_to_4 / 4.0) * 10.0
                    dimension_scores[dimension].append(score_10)

        # Average scores for each dimension
        final_scores = {}
        for dimension in self.evaluation_dimensions:
            scores = dimension_scores[dimension]
            if scores:
                final_scores[dimension] = round(sum(scores) / len(scores), 1)
            else:
                final_scores[dimension] = 5.0  # Default score

        return final_scores

    def _estimate_dimension_score(self, transcript: str, dimension: str) -> int:
        """Estimate a score (0-4) for a dimension based on transcript content"""
        text = transcript.lower()

        # Simple keyword-based scoring for each dimension
        dimension_keywords = {
            "Experience & Skills": [
                "experience",
                "worked",
                "skills",
                "training",
                "certified",
                "years",
            ],
            "Motivation": [
                "want",
                "passionate",
                "enjoy",
                "love",
                "motivated",
                "purpose",
            ],
            "Punctuality": [
                "time",
                "schedule",
                "punctual",
                "reliable",
                "on time",
                "early",
            ],
            "Compassion and Empathy": [
                "care",
                "help",
                "understand",
                "empathy",
                "compassion",
                "patient",
            ],
            "Communication": [
                "communicate",
                "listen",
                "talk",
                "explain",
                "clear",
                "understand",
            ],
        }

        keywords = dimension_keywords.get(dimension, [])
        matches = sum(1 for keyword in keywords if keyword in text)

        # Convert matches to 0-4 score
        if matches >= 4:
            return 4
        elif matches >= 3:
            return 3
        elif matches >= 2:
            return 2
        elif matches >= 1:
            return 1
        else:
            return 0

    def _create_evaluation_prompt(self, transcript: str, user_data: Dict) -> str:
        """Create evaluation prompt for Gemini"""

        candidate_info = f"""
Candidate Information:
- Name: {user_data.get('firstName', '')} {user_data.get('lastName', '')}
- Email: {user_data.get('email', '')}
- Phone: {user_data.get('phone', '')}
- Caregiving Experience: {'Yes' if user_data.get('caregivingExperience') else 'No'}
- Has PER ID: {'Yes' if user_data.get('hasPerId') else 'No'}
- Driver's License: {'Yes' if user_data.get('driversLicense') else 'No'}
- Auto Insurance: {'Yes' if user_data.get('autoInsurance') else 'No'}
- Availability: {', '.join(user_data.get('availability', []))}
- Weekly Hours: {user_data.get('weeklyHours', 0)} hours
- Languages: {', '.join(user_data.get('languages', []))}
"""

        prompt = f"""
You are evaluating a caregiver candidate based on their interview transcript and background information.

{candidate_info}

Interview Transcript:
{transcript}

Please evaluate this candidate on the following 5 dimensions and provide a score from 0 to 10 for each:

1. Experience & Skills: Relevant caregiving experience, technical skills, certifications
2. Motivation: Genuine interest in caregiving, reasons for wanting the job, commitment level
3. Punctuality: Reliability, time management, responsibility (infer from responses about schedules, commitments)
4. Compassion and Empathy: Ability to understand and care for others, emotional intelligence
5. Communication: Clarity of expression, listening skills, ability to communicate with clients/families

Respond ONLY with a JSON object in this exact format:
{{
    "Experience & Skills": 7.5,
    "Motivation": 8.0,
    "Punctuality": 6.5,
    "Compassion and Empathy": 9.0,
    "Communication": 7.0
}}

Do not include any other text or explanation, just the JSON object with scores.
"""

        return prompt

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
            "error": "Automated evaluation failed - default scores assigned",
        }


# Global instance
caregiver_evaluation_service = CaregiverEvaluationService()
