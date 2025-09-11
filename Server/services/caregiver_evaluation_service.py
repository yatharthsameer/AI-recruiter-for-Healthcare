"""
Caregiver Evaluation Service
Specialized evaluation system for home care/caregiver interviews
"""
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class CaregiverEvaluationService:
    """Service for evaluating caregiver interview performance"""
    
    def __init__(self):
        # Scoring weights for different competencies
        self.competency_weights = {
            "empathy_compassion": 0.25,
            "safety_awareness": 0.25, 
            "communication_skills": 0.20,
            "problem_solving": 0.20,
            "experience_commitment": 0.10
        }
        
        # Keyword patterns for scoring
        self.scoring_patterns = {
            "empathy": r"(empathy|empathetic|understand|understanding|compassion|compassionate|feel|feeling|emotional|emotions)",
            "patience": r"(patient|patience|calm|calmly|wait|waiting|slow|slowly|gentle|gently|take time)",
            "care": r"(care|caring|help|helping|support|supporting|assist|assisting|comfort|comforting)",
            "safety": r"(safe|safety|secure|protocol|procedure|emergency|alert|careful|cautious|report|reporting)",
            "communication": r"(listen|listening|talk|talking|explain|explaining|communicate|communication|discuss|conversation)",
            "respect": r"(respect|respectful|dignity|privacy|rights|boundaries|professional|appropriate)",
            "problem_solving": r"(solve|solution|problem|challenge|difficult|handle|manage|approach|strategy|plan)",
            "experience": r"(experience|experienced|worked|years|trained|training|certified|certification|learn|learning)",
            "commitment": r"(committed|dedication|dedicated|reliable|dependable|responsible|motivated|passion|passionate)",
            "negative": r"(angry|hate|can't|won't|never|rude|unsafe|ignore|delay|lazy|argue|frustrated|annoyed|impatient)",
            "concerns": r"(difficult|hard|struggle|struggling|stress|stressed|overwhelmed|tired|exhausted)"
        }
    
    async def evaluate_candidate(self, interview_data: Dict) -> Dict:
        """
        Comprehensive caregiver evaluation
        
        Args:
            interview_data: Dictionary containing:
                - responses: List of user responses
                - transcript: Full interview transcript
                - userData: Candidate background information
                - scoringBreakdown: Detailed scoring from interview
                - interviewDuration: Duration of interview
        
        Returns:
            Comprehensive evaluation dictionary
        """
        try:
            responses = interview_data.get('responses', [])
            transcript = interview_data.get('transcript', [])
            user_data = interview_data.get('userData', {})
            scoring_breakdown = interview_data.get('scoringBreakdown', [])
            duration = interview_data.get('interviewDuration', 0)
            
            # Calculate quantitative scores
            quantitative_scores = self._calculate_quantitative_scores(responses, scoring_breakdown, user_data)
            
            # Analyze response quality
            quality_scores = self._analyze_response_quality(responses)
            
            # Calculate competency scores
            competency_scores = self._calculate_competency_scores(quantitative_scores, responses)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(competency_scores, quality_scores)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(overall_score, competency_scores)
            
            # Identify strengths and development areas
            strengths = self._identify_strengths(competency_scores, responses, user_data)
            development_areas = self._identify_development_areas(competency_scores, responses, user_data)
            
            # Generate next steps
            next_steps = self._generate_next_steps(recommendation, overall_score, development_areas)
            
            evaluation = {
                "evaluationId": f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "overallScore": overall_score,
                "recommendation": recommendation,
                "competencyScores": competency_scores,
                "qualityScores": quality_scores,
                "quantitativeScores": quantitative_scores,
                "strengths": strengths,
                "developmentAreas": development_areas,
                "nextSteps": next_steps,
                "interviewMetrics": {
                    "duration": duration,
                    "questionsAnswered": len(responses),
                    "averageResponseLength": sum(len(r.get('response', '')) for r in responses) / max(len(responses), 1),
                    "scoringBreakdown": scoring_breakdown
                },
                "candidateProfile": self._analyze_candidate_profile(user_data)
            }
            
            logger.info(f"Caregiver evaluation completed - Score: {overall_score}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error in caregiver evaluation: {e}")
            return self._get_fallback_evaluation()
    
    def _calculate_quantitative_scores(
        self, 
        responses: List[Dict], 
        scoring_breakdown: List[Dict], 
        user_data: Dict = None
    ) -> Dict:
        """Calculate quantitative scores from responses"""
        
        scores = {
            "empathy": 0,
            "patience": 0,
            "care": 0,
            "safety": 0,
            "communication": 0,
            "respect": 0,
            "problem_solving": 0,
            "experience": 0,
            "commitment": 0,
            "negative": 0,
            "concerns": 0
        }
        
        # Analyze text responses
        all_text = " ".join([r.get('response', '') for r in responses]).lower()
        
        for category, pattern in self.scoring_patterns.items():
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            scores[category] = len(matches)
        
        # Add bonus points for background qualifications
        if user_data:
            if user_data.get('hhaExperience'):
                scores['experience'] += 5
            if user_data.get('cprCertified'):
                scores['safety'] += 3
            if user_data.get('driversLicense') and user_data.get('reliableTransport'):
                scores['commitment'] += 2
        
        # Use scoring breakdown if available
        if scoring_breakdown:
            for breakdown in scoring_breakdown:
                detail = breakdown.get('breakdown', {})
                for key, value in detail.items():
                    if key in scores:
                        scores[key] += value
        
        return scores
    
    def _analyze_response_quality(self, responses: List[Dict]) -> Dict:
        """Analyze the quality of responses"""
        
        if not responses:
            return {"relevance": 0, "clarity": 0, "depth": 0}
        
        total_relevance = 0
        total_clarity = 0
        total_depth = 0
        
        for i, response in enumerate(responses):
            text = response.get('response', '')
            
            # Calculate relevance score (0-10)
            relevance = self._calculate_relevance_score(text, i + 1)
            
            # Calculate clarity score (0-10)
            clarity = self._calculate_clarity_score(text)
            
            # Calculate depth score (0-10)
            depth = min(10, len(text.split()) / 10)  # 10 words = 1 point, max 10
            
            total_relevance += relevance
            total_clarity += clarity
            total_depth += depth
        
        count = len(responses)
        return {
            "relevance": round(total_relevance / count, 1),
            "clarity": round(total_clarity / count, 1),
            "depth": round(total_depth / count, 1)
        }
    
    def _calculate_relevance_score(self, text: str, question_number: int) -> float:
        """Calculate how relevant the response is to caregiving"""
        
        caregiving_keywords = [
            "patient", "client", "care", "help", "assist", "support",
            "medication", "safety", "emergency", "family", "comfort",
            "listen", "understand", "respect", "dignity", "professional"
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in caregiving_keywords if keyword in text_lower)
        
        # Base score from keyword density
        base_score = min(8, keyword_count * 1.5)
        
        # Bonus for specific examples
        if any(phrase in text_lower for phrase in ["time when", "example", "situation", "experience"]):
            base_score += 1
        
        # Penalty for very short responses
        if len(text.split()) < 5:
            base_score *= 0.5
        
        return min(10, base_score)
    
    def _calculate_clarity_score(self, text: str) -> float:
        """Calculate clarity and coherence of response"""
        
        if not text or len(text.strip()) < 10:
            return 0
        
        words = text.split()
        sentences = text.split('.')
        
        # Base score
        score = 5
        
        # Length appropriateness (not too short, not too long)
        word_count = len(words)
        if 20 <= word_count <= 100:
            score += 2
        elif 10 <= word_count < 20 or 100 < word_count <= 150:
            score += 1
        elif word_count < 10:
            score -= 2
        
        # Sentence structure
        avg_sentence_length = len(words) / max(len(sentences), 1)
        if 8 <= avg_sentence_length <= 20:
            score += 1
        
        # Grammar indicators (simple heuristics)
        if text.count(',') > 0:  # Use of commas
            score += 0.5
        if any(word in text.lower() for word in ['because', 'since', 'although', 'however']):
            score += 0.5  # Complex sentence structures
        
        return min(10, score)
    
    def _calculate_competency_scores(self, quantitative_scores: Dict, responses: List[Dict]) -> Dict:
        """Calculate scores for each competency area"""
        
        # Empathy & Compassion (0-10)
        empathy_raw = quantitative_scores['empathy'] * 2 + quantitative_scores['care']
        empathy_score = min(10, empathy_raw)
        
        # Safety Awareness (0-10)
        safety_raw = quantitative_scores['safety'] * 2 + quantitative_scores['experience'] * 0.5
        safety_score = min(10, safety_raw)
        
        # Communication Skills (0-10)
        comm_raw = quantitative_scores['communication'] + quantitative_scores['respect']
        comm_score = min(10, comm_raw)
        
        # Problem-Solving (0-10)
        problem_raw = quantitative_scores['problem_solving'] * 1.5
        problem_score = min(10, problem_raw)
        
        # Experience & Commitment (0-10)
        exp_raw = quantitative_scores['experience'] + quantitative_scores['commitment']
        exp_score = min(10, exp_raw)
        
        # Apply penalties for negative indicators
        negative_penalty = quantitative_scores['negative'] * 0.5
        concern_penalty = quantitative_scores['concerns'] * 0.2
        
        return {
            "empathy_compassion": max(0, empathy_score - negative_penalty),
            "safety_awareness": max(0, safety_score - concern_penalty),
            "communication_skills": max(0, comm_score - negative_penalty),
            "problem_solving": max(0, problem_score - concern_penalty),
            "experience_commitment": max(0, exp_score - negative_penalty)
        }
    
    def _calculate_overall_score(self, competency_scores: Dict, quality_scores: Dict) -> int:
        """Calculate overall score (0-100)"""
        
        # Weighted competency score
        competency_total = sum(
            score * self.competency_weights[competency]
            for competency, score in competency_scores.items()
        )
        
        # Quality bonus/penalty
        quality_avg = sum(quality_scores.values()) / len(quality_scores)
        quality_factor = quality_avg / 10  # Convert to 0-1 scale
        
        # Final score calculation
        base_score = competency_total * 10  # Convert to 0-100 scale
        final_score = base_score * (0.8 + 0.2 * quality_factor)  # Quality affects 20%
        
        return max(0, min(100, round(final_score)))
    
    def _generate_recommendation(self, overall_score: int, competency_scores: Dict) -> Dict:
        """Generate hiring recommendation based on scores"""
        
        # Check for critical competency failures
        critical_competencies = ["empathy_compassion", "safety_awareness"]
        critical_failure = any(
            competency_scores[comp] < 3 for comp in critical_competencies
        )
        
        if critical_failure or overall_score < 40:
            recommendation = "Not Recommended"
            confidence = "High"
            reasoning = "Critical competency gaps identified that pose risks to client safety and care quality."
        elif overall_score >= 80:
            recommendation = "Highly Recommended"
            confidence = "High"
            reasoning = "Strong performance across all competency areas with excellent caregiving potential."
        elif overall_score >= 65:
            recommendation = "Recommended"
            confidence = "Medium" if overall_score < 75 else "High"
            reasoning = "Good overall performance with minor areas for development."
        else:
            recommendation = "Consider with Training"
            confidence = "Medium"
            reasoning = "Shows potential but requires targeted training before placement."
        
        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning": reasoning,
            "score": overall_score
        }
    
    def _identify_strengths(
        self, 
        competency_scores: Dict, 
        responses: List[Dict], 
        user_data: Dict = None
    ) -> List[str]:
        """Identify candidate strengths"""
        
        strengths = []
        
        # Competency-based strengths
        for competency, score in competency_scores.items():
            if score >= 7:
                competency_name = competency.replace('_', ' ').title()
                strengths.append(f"Strong {competency_name} ({score}/10)")
        
        # Background-based strengths
        if user_data:
            if user_data.get('hhaExperience'):
                strengths.append("Relevant HHA experience")
            if user_data.get('cprCertified'):
                strengths.append("CPR certified for emergency response")
            if user_data.get('driversLicense') and user_data.get('reliableTransport'):
                strengths.append("Reliable transportation for client visits")
            if user_data.get('availability'):
                strengths.append(f"Available {', '.join(user_data['availability'])}")
        
        # Response-based strengths
        response_text = " ".join([r.get('response', '') for r in responses]).lower()
        
        if any(word in response_text for word in ['example', 'experience', 'situation']):
            strengths.append("Provides specific examples from experience")
        
        if len(response_text.split()) > 200:
            strengths.append("Detailed and thorough responses")
        
        return strengths[:5]  # Limit to top 5 strengths
    
    def _identify_development_areas(
        self, 
        competency_scores: Dict, 
        responses: List[Dict], 
        user_data: Dict = None
    ) -> List[str]:
        """Identify areas needing development"""
        
        development_areas = []
        
        # Competency-based development areas
        for competency, score in competency_scores.items():
            if score < 5:
                competency_name = competency.replace('_', ' ').title()
                development_areas.append(f"Needs improvement in {competency_name} ({score}/10)")
        
        # Response quality issues
        avg_response_length = sum(len(r.get('response', '')) for r in responses) / max(len(responses), 1)
        
        if avg_response_length < 50:
            development_areas.append("Responses lack detail and specific examples")
        
        # Background gaps
        if user_data:
            if not user_data.get('hhaExperience'):
                development_areas.append("No formal HHA experience - requires training")
            if not user_data.get('cprCertified'):
                development_areas.append("CPR certification needed for safety compliance")
        
        return development_areas[:5]  # Limit to top 5 areas
    
    def _generate_next_steps(
        self, 
        recommendation: Dict, 
        overall_score: int, 
        development_areas: List[str]
    ) -> List[str]:
        """Generate recommended next steps"""
        
        next_steps = []
        
        rec_type = recommendation['recommendation']
        
        if rec_type == "Highly Recommended":
            next_steps.extend([
                "Proceed with reference checks and background verification",
                "Schedule orientation and onboarding process",
                "Assign to experienced mentor for first few client visits"
            ])
        elif rec_type == "Recommended":
            next_steps.extend([
                "Conduct reference checks to verify experience claims",
                "Provide brief refresher training on identified development areas",
                "Consider probationary period with regular check-ins"
            ])
        elif rec_type == "Consider with Training":
            next_steps.extend([
                "Enroll in comprehensive HHA training program",
                "Schedule follow-up interview after training completion",
                "Require supervised practice before independent assignments"
            ])
        else:  # Not Recommended
            next_steps.extend([
                "Provide feedback on specific areas needing improvement",
                "Recommend formal caregiving education or certification program",
                "Consider re-application after 6-12 months of relevant experience"
            ])
        
        # Add specific steps based on development areas
        if any("CPR" in area for area in development_areas):
            next_steps.append("Obtain CPR certification before placement")
        
        if any("communication" in area.lower() for area in development_areas):
            next_steps.append("Provide communication skills training")
        
        return next_steps[:6]  # Limit to 6 steps
    
    def _analyze_candidate_profile(self, user_data: Dict) -> Dict:
        """Analyze candidate background profile"""
        
        profile_score = 0
        profile_notes = []
        
        if user_data.get('hhaExperience'):
            profile_score += 30
            profile_notes.append("Has HHA experience")
        
        if user_data.get('cprCertified'):
            profile_score += 20
            profile_notes.append("CPR certified")
        
        if user_data.get('driversLicense'):
            profile_score += 15
            profile_notes.append("Has driver's license")
        
        if user_data.get('reliableTransport'):
            profile_score += 15
            profile_notes.append("Has reliable transportation")
        
        if user_data.get('availability'):
            profile_score += 10
            profile_notes.append(f"Available {len(user_data['availability'])} time slots")
        
        weekly_hours = user_data.get('weeklyHours', 0)
        if weekly_hours >= 20:
            profile_score += 10
            profile_notes.append(f"Seeking {weekly_hours} hours/week")
        
        return {
            "profileScore": min(100, profile_score),
            "profileNotes": profile_notes,
            "readinessLevel": "High" if profile_score >= 70 else "Medium" if profile_score >= 40 else "Low"
        }
    
    def _get_fallback_evaluation(self) -> Dict:
        """Return fallback evaluation when processing fails"""
        return {
            "evaluationId": f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "overallScore": 50,
            "recommendation": {
                "recommendation": "Consider with Training",
                "confidence": "Low",
                "reasoning": "Unable to complete full evaluation - manual review recommended",
                "score": 50
            },
            "competencyScores": {
                "empathy_compassion": 5,
                "safety_awareness": 5,
                "communication_skills": 5,
                "problem_solving": 5,
                "experience_commitment": 5
            },
            "qualityScores": {
                "relevance": 5,
                "clarity": 5,
                "depth": 5
            },
            "strengths": ["Completed interview process"],
            "developmentAreas": ["Requires comprehensive evaluation"],
            "nextSteps": ["Schedule follow-up interview", "Conduct manual evaluation"],
            "error": "Automated evaluation failed - manual review required"
        }

# Global instance
caregiver_evaluation_service = CaregiverEvaluationService()
