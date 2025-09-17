"""
Simple Topic Coverage Tracker
Tracks whether the 9 core interview topics have been covered naturally
"""

import logging
from typing import Dict, List, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TopicInfo:
    """Information about a required interview topic"""
    id: str
    name: str
    description: str
    keywords: List[str]  # Keywords that might indicate this topic was covered
    evaluation_dimension: str
    standardized_question: str  # The exact question to ask for this topic

class TopicCoverageTracker:
    """Simple tracker for ensuring all required interview topics are eventually covered"""
    
    def __init__(self):
        # Define the 9 core topics we need to cover with standardized questions
        self.required_topics = {
            "caregiver_experience": TopicInfo(
                id="caregiver_experience",
                name="Caregiver Experience",
                description="Previous experience working as a caregiver",
                keywords=["caregiver", "worked", "experience", "patients", "clients", "nursing", "care", "assisted living"],
                evaluation_dimension="Experience & Skills",
                standardized_question="Have you ever worked as a caregiver? If so, can you please share what kind of patients/customers you worked with and what services or activities you performed?"
            ),
            "important_traits": TopicInfo(
                id="important_traits",
                name="Important Caregiver Traits",
                description="What traits/skills are important for caregivers",
                keywords=["traits", "skills", "important", "qualities", "good caregiver", "empathy", "patience"],
                evaluation_dimension="Experience & Skills",
                standardized_question="Imagine that you're finding a caregiver for one of your loved ones. What traits or skills would be most important to you for this caregiver to have?"
            ),
            "skill_building": TopicInfo(
                id="skill_building",
                name="Skill Development",
                description="How prior experience built caregiving skills",
                keywords=["skills", "experience", "learned", "developed", "built", "training", "background"],
                evaluation_dimension="Experience & Skills",
                standardized_question="Describe for me how your prior work or life experience has helped you build the skills necessary to be a good caregiver?"
            ),
            "motivation": TopicInfo(
                id="motivation",
                name="Motivation for Caregiving",
                description="Why they want to be a caregiver, what's rewarding",
                keywords=["why", "motivation", "rewarding", "fulfilling", "passion", "help", "care", "meaningful"],
                evaluation_dimension="Motivation",
                standardized_question="Why do you want to be a caregiver? What are the most rewarding aspects of the job?"
            ),
            "lateness_problems": TopicInfo(
                id="lateness_problems",
                name="Punctuality Challenges",
                description="Times when being late caused problems",
                keywords=["late", "punctuality", "time", "problems", "team", "learned", "mistake"],
                evaluation_dimension="Punctuality",
                standardized_question="Tell me about a time when being late caused problems for you or your team. What did you learn from it?"
            ),
            "punctuality_adjustments": TopicInfo(
                id="punctuality_adjustments",
                name="Punctuality Improvements",
                description="Adjustments made to ensure punctuality",
                keywords=["routine", "punctuality", "time", "changes", "early", "schedule", "reliable"],
                evaluation_dimension="Punctuality",
                standardized_question="Have you ever had to adjust your routine to ensure punctuality at work? What changes did you make?"
            ),
            "senior_care_experience": TopicInfo(
                id="senior_care_experience",
                name="Senior Care Experience",
                description="Experience caring for seniors, challenges and meaningful moments",
                keywords=["senior", "elderly", "difficult", "meaningful", "challenging", "rewarding", "grandmother", "grandfather"],
                evaluation_dimension="Compassion and Empathy",
                standardized_question="Tell me about a time when you cared for a senior. What part of the experience was most difficult and what was most meaningful to you?"
            ),
            "helping_struggling_person": TopicInfo(
                id="helping_struggling_person",
                name="Helping Others in Need",
                description="Helping colleague or client who was struggling",
                keywords=["helped", "colleague", "client", "struggling", "emotional", "support", "listened"],
                evaluation_dimension="Compassion and Empathy",
                standardized_question="Tell me about a time when you helped a colleague or client who was struggling emotionally or professionally. What did you do?"
            ),
            "coworker_feedback": TopicInfo(
                id="coworker_feedback",
                name="Self-Awareness & Reputation",
                description="What coworkers would say about them",
                keywords=["coworkers", "colleagues", "say about", "three things", "reputation", "reliable", "team"],
                evaluation_dimension="Communication",
                standardized_question="If we were to ask your co-workers about you, what are the three things they would say?"
            )
        }
        
        # Track which topics have been covered
        self.covered_topics: Dict[str, bool] = {topic_id: False for topic_id in self.required_topics.keys()}
        self.topic_evidence: Dict[str, List[str]] = {topic_id: [] for topic_id in self.required_topics.keys()}
    
    def analyze_response_coverage(self, response_text: str, question_context: str = "") -> List[str]:
        """
        Analyze a response to see which topics it might cover
        Returns list of topic IDs that were likely covered
        """
        covered_in_response = []
        response_lower = response_text.lower()
        context_lower = question_context.lower()
        combined_text = f"{response_lower} {context_lower}"
        
        for topic_id, topic_info in self.required_topics.items():
            # Check if response contains keywords for this topic
            keyword_matches = sum(1 for keyword in topic_info.keywords if keyword in combined_text)
            
            # If we find multiple keywords or strong indicators, mark as covered
            if keyword_matches >= 2 or self._has_strong_indicators(topic_id, combined_text):
                if not self.covered_topics[topic_id]:  # Only log if newly covered
                    logger.info(f"📋 Topic covered: {topic_info.name} (keywords: {keyword_matches})")
                
                self.covered_topics[topic_id] = True
                self.topic_evidence[topic_id].append(response_text[:200] + "..." if len(response_text) > 200 else response_text)
                covered_in_response.append(topic_id)
        
        return covered_in_response
    
    def _has_strong_indicators(self, topic_id: str, text: str) -> bool:
        """Check for strong indicators that a topic was covered"""
        strong_indicators = {
            "caregiver_experience": ["worked as", "nursing home", "assisted living", "home care", "cna", "aide"],
            "motivation": ["want to be", "passionate about", "love helping", "rewarding", "fulfilling"],
            "lateness_problems": ["was late", "being late", "caused problems", "learned from"],
            "punctuality_adjustments": ["adjust", "routine", "ensure", "on time", "early"],
            "senior_care_experience": ["cared for", "grandmother", "grandfather", "elderly", "senior"],
            "helping_struggling_person": ["helped", "colleague", "struggling", "emotional support"],
            "coworker_feedback": ["coworkers would say", "colleagues say", "three things"]
        }
        
        indicators = strong_indicators.get(topic_id, [])
        return any(indicator in text for indicator in indicators)
    
    def mark_topic_covered(self, topic_id: str, evidence: str = ""):
        """Manually mark a topic as covered"""
        if topic_id in self.required_topics:
            self.covered_topics[topic_id] = True
            if evidence:
                self.topic_evidence[topic_id].append(evidence)
            logger.info(f"📋 Manually marked topic as covered: {self.required_topics[topic_id].name}")
    
    def get_missing_topics(self) -> List[TopicInfo]:
        """Get list of topics that haven't been covered yet"""
        return [
            self.required_topics[topic_id] 
            for topic_id, covered in self.covered_topics.items() 
            if not covered
        ]
    
    def get_covered_topics(self) -> List[TopicInfo]:
        """Get list of topics that have been covered"""
        return [
            self.required_topics[topic_id] 
            for topic_id, covered in self.covered_topics.items() 
            if covered
        ]
    
    def is_complete(self) -> bool:
        """Check if all required topics have been covered"""
        return all(self.covered_topics.values())
    
    def get_completion_percentage(self) -> float:
        """Get percentage of topics covered"""
        covered_count = sum(1 for covered in self.covered_topics.values() if covered)
        return (covered_count / len(self.required_topics)) * 100
    
    def get_coverage_summary(self) -> Dict:
        """Get a summary of coverage status"""
        covered = self.get_covered_topics()
        missing = self.get_missing_topics()
        
        return {
            "total_topics": len(self.required_topics),
            "covered_count": len(covered),
            "missing_count": len(missing),
            "completion_percentage": self.get_completion_percentage(),
            "is_complete": self.is_complete(),
            "covered_topics": [{"id": t.id, "name": t.name, "dimension": t.evaluation_dimension} for t in covered],
            "missing_topics": [{"id": t.id, "name": t.name, "dimension": t.evaluation_dimension} for t in missing],
            "dimension_coverage": self._get_dimension_coverage()
        }
    
    def get_required_questions_for_missing_topics(self) -> List[str]:
        """Get the standardized questions for topics that haven't been covered yet"""
        missing_topics = self.get_missing_topics()
        return [topic.standardized_question for topic in missing_topics]
    
    def _get_dimension_coverage(self) -> Dict[str, Dict]:
        """Get coverage by evaluation dimension"""
        dimensions = {}
        
        for topic_info in self.required_topics.values():
            dim = topic_info.evaluation_dimension
            if dim not in dimensions:
                dimensions[dim] = {"total": 0, "covered": 0, "topics": []}
            
            dimensions[dim]["total"] += 1
            dimensions[dim]["topics"].append({
                "id": topic_info.id,
                "name": topic_info.name,
                "covered": self.covered_topics[topic_info.id]
            })
            
            if self.covered_topics[topic_info.id]:
                dimensions[dim]["covered"] += 1
        
        # Add completion percentage for each dimension
        for dim_info in dimensions.values():
            dim_info["completion_percentage"] = (dim_info["covered"] / dim_info["total"]) * 100
        
        return dimensions
    
    def reset(self):
        """Reset all coverage tracking"""
        self.covered_topics = {topic_id: False for topic_id in self.required_topics.keys()}
        self.topic_evidence = {topic_id: [] for topic_id in self.required_topics.keys()}
        logger.info("📋 Coverage tracker reset")

# Global instance
topic_coverage_tracker = TopicCoverageTracker()
