-- Seed Reference Answers for RAG System
-- Insert excellent, good, fair, and poor reference answers directly into database

-- Q1: Caregiver Experience
INSERT INTO expected_answers (id, question_id, answer_text, quality_level, score_range_min, score_range_max, empathy_indicators, experience_indicators, behavioral_patterns, embedding_id) VALUES

-- EXCELLENT ANSWERS for Q1
('Q1_excellent_001', 'Q1', 'I worked as a certified nursing assistant for 3 years at Sunrise Senior Living. I cared for residents with various conditions including dementia, diabetes, and mobility issues. My daily responsibilities included assisting with personal care, medication reminders, meal assistance, and providing emotional support. I helped with transfers using proper body mechanics and gait belts, and I was trained in infection control protocols. What I found most rewarding was building relationships with residents and seeing how small acts of kindness could brighten their day.', 'excellent', 90, 100, 
'["compassion", "relationships", "kindness", "emotional_support", "rewarding"]', 
'["CNA_certification", "3_years", "diverse_conditions", "technical_skills", "infection_control"]', 
'["specific_duties", "professional_training", "measurable_outcomes", "relationship_building"]', 
'Q1_excellent_001_embedding'),

('Q1_excellent_002', 'Q1', 'I have 5 years of experience as a home health aide working with elderly clients. I assisted clients with Alzheimers, Parkinsons, and post-stroke recovery. My services included personal hygiene assistance, meal preparation, light housekeeping, medication management, and companionship. I was trained in fall prevention and emergency response. I also helped families by providing regular updates on their loved ones condition and needs. The most meaningful part was helping clients maintain their independence and dignity in their own homes.', 'excellent', 90, 100,
'["dignity", "independence", "companionship", "family_support", "meaningful"]',
'["5_years", "home_health", "multiple_conditions", "emergency_training", "medication_management"]',
'["comprehensive_care", "family_communication", "independence_focus", "professional_updates"]',
'Q1_excellent_002_embedding'),

-- GOOD ANSWERS for Q1
('Q1_good_001', 'Q1', 'I worked as a caregiver for about 2 years at a nursing home. I helped elderly residents with daily activities like bathing, dressing, and eating. I also did some light cleaning and cooking. I enjoyed talking with them and making sure they were comfortable. It was rewarding to help people who needed assistance with basic tasks.', 'good', 75, 89,
'["enjoyed", "comfortable", "rewarding", "help"]',
'["2_years", "nursing_home", "daily_activities", "basic_care"]',
'["basic_duties", "general_satisfaction", "routine_care"]',
'Q1_good_001_embedding'),

-- FAIR ANSWERS for Q1  
('Q1_fair_001', 'Q1', 'I helped take care of my grandfather for a few months when he was sick. I made sure he took his medicine and helped him get around the house. It was okay, but sometimes it was difficult when he was confused and didnt want to cooperate.', 'fair', 60, 74,
'["helped", "care"]',
'["few_months", "basic_assistance", "medication_help"]',
'["personal_experience", "limited_scope", "basic_tasks"]',
'Q1_fair_001_embedding'),

-- POOR ANSWERS for Q1
('Q1_poor_001', 'Q1', 'No, I havent worked as a caregiver before, but I think I would be good at it because Im a nice person and I care about people.', 'poor', 0, 59,
'["nice", "care"]',
'[]',
'["no_experience", "vague_response", "assumptions"]',
'Q1_poor_001_embedding');

-- Q2: Ideal Caregiver Traits  
INSERT INTO expected_answers (id, question_id, answer_text, quality_level, score_range_min, score_range_max, empathy_indicators, experience_indicators, behavioral_patterns, embedding_id) VALUES

-- EXCELLENT ANSWERS for Q2
('Q2_excellent_001', 'Q2', 'For my loved one, I would want a caregiver who is patient, compassionate, and reliable. They should have experience with the specific condition my family member has, whether thats dementia, mobility issues, or chronic illness. Communication skills are crucial - they need to listen to my loved one and keep our family informed. I would also want someone who respects their dignity and independence, encouraging them to do what they can while providing help where needed. Trust and honesty are essential because were inviting this person into our most vulnerable moments.', 'excellent', 90, 100,
'["patient", "compassionate", "dignity", "respect", "trust", "understanding"]',
'["specific_condition_experience", "communication_skills", "family_involvement", "professional_boundaries"]',
'["comprehensive_thinking", "family_perspective", "trust_building", "independence_focus"]',
'Q2_excellent_001_embedding'),

-- GOOD ANSWERS for Q2
('Q2_good_001', 'Q2', 'I would want someone who is kind, patient, and experienced. They should know how to help with medical needs and be able to communicate well. Its important that they treat my family member with respect and understand their individual needs.', 'good', 75, 89,
'["kind", "patient", "respect", "understanding"]',
'["experienced", "medical_needs", "communication", "individual_needs"]',
'["basic_qualities", "practical_focus", "respect_emphasis"]',
'Q2_good_001_embedding'),

-- FAIR ANSWERS for Q2
('Q2_fair_001', 'Q2', 'Someone who is nice and can help with basic things like cooking and cleaning. They should be friendly and not get frustrated easily.', 'fair', 60, 74,
'["nice", "friendly", "not_frustrated"]',
'["basic_help", "cooking", "cleaning"]',
'["surface_level", "basic_tasks", "limited_insight"]',
'Q2_fair_001_embedding'),

-- POOR ANSWERS for Q2
('Q2_poor_001', 'Q2', 'Just someone who shows up on time and does their job.', 'poor', 0, 59,
'[]',
'["shows_up", "does_job"]',
'["minimal_expectations", "transactional_view", "no_empathy"]',
'Q2_poor_001_embedding');

-- Q7: Senior Care Experience
INSERT INTO expected_answers (id, question_id, answer_text, quality_level, score_range_min, score_range_max, empathy_indicators, experience_indicators, behavioral_patterns, embedding_id) VALUES

-- EXCELLENT ANSWERS for Q7
('Q7_excellent_001', 'Q7', 'I cared for my grandmother with dementia for two years after she moved in with us. The most difficult part was watching her confusion and frustration, especially during sundowning episodes. She would sometimes not recognize me or become agitated. I learned to stay calm, use simple words, and redirect her attention to activities she enjoyed like looking at old photos. The most meaningful part was realizing that even though her memory was fading, her emotions and need for connection remained. When I played her favorite music or held her hand, I could see glimpses of the grandmother I knew. It taught me that dignity and respect are crucial in caregiving, and that the person is still there even when the disease progresses.', 'excellent', 90, 100,
'["patience", "dignity", "emotional_intelligence", "person_centered_care", "understanding", "respect", "connection"]',
'["2_years_experience", "dementia_care", "behavioral_management", "adaptive_strategies", "sundowning_knowledge"]',
'["situation_personal", "challenges_acknowledged", "actions_compassionate", "learning_demonstrated", "meaningful_insights"]',
'Q7_excellent_001_embedding'),

('Q7_excellent_002', 'Q7', 'I worked with an 89-year-old client with Parkinsons disease for 8 months. The most challenging aspect was helping him maintain his independence while ensuring his safety during mobility issues and tremors. Some days his symptoms were worse, making simple tasks like eating or dressing very frustrating for him. I learned to be patient, break tasks into smaller steps, and celebrate small victories with him. The most meaningful part was seeing his face light up when he successfully completed a task on his own, even if it took longer. It reinforced for me that preserving dignity and autonomy is just as important as providing physical care.', 'excellent', 90, 100,
'["patience", "independence", "dignity", "autonomy", "understanding", "celebration", "empathy"]',
'["8_months", "Parkinsons_care", "mobility_assistance", "symptom_management", "adaptive_techniques"]',
'["professional_experience", "challenge_identification", "adaptive_strategies", "dignity_focus", "meaningful_reflection"]',
'Q7_excellent_002_embedding'),

-- GOOD ANSWERS for Q7
('Q7_good_001', 'Q7', 'I took care of my neighbors mother who had mobility issues after a fall. The difficult part was helping her with personal care because she was embarrassed about needing help. I tried to be respectful and let her do as much as she could on her own. The meaningful part was seeing her confidence return as she got stronger. She would tell me stories about her life, and I learned a lot from her wisdom.', 'good', 75, 89,
'["respectful", "confidence", "wisdom", "dignity", "understanding"]',
'["mobility_issues", "personal_care", "recovery_support", "independence_encouragement"]',
'["respect_for_independence", "relationship_building", "learning_attitude", "gradual_improvement"]',
'Q7_good_001_embedding'),

-- FAIR ANSWERS for Q7
('Q7_fair_001', 'Q7', 'I helped my aunt when she was sick for a couple weeks. It was hard because she was grumpy and didnt want help with anything. But I felt good when I could make her feel better by bringing her food and keeping her company.', 'fair', 60, 74,
'["felt_good", "company", "help"]',
'["couple_weeks", "basic_assistance", "companionship"]',
'["personal_experience", "basic_care", "simple_comfort"]',
'Q7_fair_001_embedding'),

-- POOR ANSWERS for Q7
('Q7_poor_001', 'Q7', 'I dont have much experience with seniors, but I think I would be patient with them because old people need help.', 'poor', 0, 59,
'["patient"]',
'[]',
'["no_experience", "hypothetical_response", "stereotypical_thinking"]',
'Q7_poor_001_embedding');

-- Q8: Emotional Support
INSERT INTO expected_answers (id, question_id, answer_text, quality_level, score_range_min, score_range_max, empathy_indicators, experience_indicators, behavioral_patterns, embedding_id) VALUES

-- EXCELLENT ANSWERS for Q8
('Q8_excellent_001', 'Q8', 'A colleague was struggling after losing a patient she had cared for over several months. She was questioning whether she was cut out for this work. I sat with her during our break and just listened while she talked about her feelings. I validated that its normal to grieve when we lose someone weve cared for - it shows were human and that we truly care. I shared that the patient had often mentioned how much my colleagues kindness meant to her. I offered to help with her workload for a few days while she processed her grief. Later, I connected her with our employee assistance program for additional support.', 'excellent', 90, 100,
'["listening", "validation", "emotional_support", "understanding", "compassion", "empathy", "grief_support"]',
'["workplace_support", "grief_understanding", "resource_connection", "professional_boundaries", "team_support"]',
'["active_listening", "emotional_validation", "practical_support", "professional_resources", "follow_up_care"]',
'Q8_excellent_001_embedding'),

-- GOOD ANSWERS for Q8
('Q8_good_001', 'Q8', 'A coworker was having trouble with a difficult client who was always complaining. She was getting frustrated and upset. I talked to her and suggested some ways to handle the situation, like staying calm and trying to understand why the client might be acting that way. I also offered to help her with that client when I could.', 'good', 75, 89,
'["understanding", "calm", "help", "support"]',
'["workplace_support", "problem_solving", "teamwork", "client_management"]',
'["advice_giving", "practical_support", "collaborative_approach", "situation_analysis"]',
'Q8_good_001_embedding'),

-- FAIR ANSWERS for Q8
('Q8_fair_001', 'Q8', 'My friend was sad about something at work. I told her it would be okay and that she shouldnt worry about it. I tried to cheer her up by taking her out for coffee after work.', 'fair', 60, 74,
'["cheer_up", "support", "comfort"]',
'["basic_support", "social_support"]',
'["simple_comfort", "distraction_approach", "social_solution"]',
'Q8_fair_001_embedding'),

-- POOR ANSWERS for Q8
('Q8_poor_001', 'Q8', 'I havent really had to deal with that situation, but I would probably just tell them to get over it and focus on their job. People need to be professional at work.', 'poor', 0, 59,
'[]',
'[]',
'["no_experience", "dismissive_approach", "lack_of_empathy", "unprofessional_advice"]',
'Q8_poor_001_embedding');

-- Q4: Motivation
INSERT INTO expected_answers (id, question_id, answer_text, quality_level, score_range_min, score_range_max, empathy_indicators, experience_indicators, behavioral_patterns, embedding_id) VALUES

-- EXCELLENT ANSWERS for Q4
('Q4_excellent_001', 'Q4', 'I want to be a caregiver because I believe everyone deserves to age with dignity and receive compassionate care. After caring for my own family members, I realized how much impact a caring person can have on someones quality of life. The most rewarding aspect is building meaningful relationships with clients and their families, knowing that Im helping someone feel safe, valued, and heard. I also find it fulfilling to help people maintain their independence for as long as possible. Even small things like helping someone stay in their own home or continue a hobby they love can make a huge difference in their happiness and well-being.', 'excellent', 90, 100,
'["dignity", "compassion", "meaningful_relationships", "valued", "independence", "happiness", "well_being"]',
'["family_care_experience", "quality_of_life_focus", "client_family_relationships", "independence_support"]',
'["personal_motivation", "specific_examples", "impact_awareness", "holistic_care_view"]',
'Q4_excellent_001_embedding'),

-- GOOD ANSWERS for Q4
('Q4_good_001', 'Q4', 'I want to be a caregiver because I enjoy helping people and making a difference in their lives. I find it rewarding when I can help someone feel better or more comfortable. I like working with elderly people because they have so much wisdom and life experience to share.', 'good', 75, 89,
'["enjoy_helping", "making_difference", "rewarding", "comfortable", "wisdom"]',
'["helping_people", "elderly_work", "life_experience"]',
'["general_motivation", "positive_attitude", "appreciation_for_elderly"]',
'Q4_good_001_embedding'),

-- FAIR ANSWERS for Q4
('Q4_fair_001', 'Q4', 'I need a job and this seems like something I could do. I think helping people is nice and the pay is okay.', 'fair', 60, 74,
'["helping", "nice"]',
'["job_seeking"]',
'["transactional_motivation", "basic_interest", "financial_focus"]',
'Q4_fair_001_embedding'),

-- POOR ANSWERS for Q4
('Q4_poor_001', 'Q4', 'I just need work and this job is available. I dont really know what else to do.', 'poor', 0, 59,
'[]',
'[]',
'["desperate_job_seeking", "no_genuine_interest", "lack_of_purpose"]',
'Q4_poor_001_embedding');

-- Q5: Punctuality Problems
INSERT INTO expected_answers (id, question_id, answer_text, quality_level, score_range_min, score_range_max, empathy_indicators, experience_indicators, behavioral_patterns, embedding_id) VALUES

-- EXCELLENT ANSWERS for Q5
('Q5_excellent_001', 'Q5', 'I was late to work one morning because of an unexpected traffic accident on my usual route. This caused our morning shift to be short-staffed during medication time, which put extra pressure on my colleagues and delayed some residents breakfast schedule. I immediately apologized to my supervisor and team, and I stayed late that day to help catch up on tasks. I learned that I needed to have backup routes planned and leave earlier to account for unexpected delays. Since then, I always check traffic conditions before leaving and have alternative routes mapped out. I also got my supervisors contact information so I can call ahead if Im ever running late again.', 'excellent', 90, 100,
'["apologized", "responsibility", "team_consideration", "learning"]',
'["accountability", "problem_solving", "planning", "communication", "reliability_improvement"]',
'["situation_specific", "impact_acknowledged", "actions_corrective", "prevention_strategies", "professional_communication"]',
'Q5_excellent_001_embedding'),

-- GOOD ANSWERS for Q5
('Q5_good_001', 'Q5', 'I was late to a team meeting once because I underestimated how long it would take to get there. My team had to start without me and I missed important information about new procedures. I apologized and made sure to get the information I missed. I learned to plan better and give myself more time to get places.', 'good', 75, 89,
'["apologized", "responsibility"]',
'["planning", "time_management", "information_seeking"]',
'["acknowledgment", "basic_learning", "improvement_effort"]',
'Q5_good_001_embedding'),

-- FAIR ANSWERS for Q5
('Q5_fair_001', 'Q5', 'I was late to work a few times because of traffic. My boss wasnt happy about it. I try to leave earlier now.', 'fair', 60, 74,
'[]',
'["traffic_excuse", "basic_adjustment"]',
'["minimal_accountability", "simple_solution", "external_blame"]',
'Q5_fair_001_embedding'),

-- POOR ANSWERS for Q5
('Q5_poor_001', 'Q5', 'I dont think Ive ever been late to anything important. If I was, it probably wasnt my fault.', 'poor', 0, 59,
'[]',
'[]',
'["denial", "blame_avoidance", "lack_of_accountability"]',
'Q5_poor_001_embedding');

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_expected_answers_question_quality ON expected_answers(question_id, quality_level);
CREATE INDEX IF NOT EXISTS idx_expected_answers_quality_score ON expected_answers(quality_level, score_range_min);

-- Update the schema to include this seed data
COMMENT ON TABLE expected_answers IS 'Reference answers for RAG system with excellent, good, fair, and poor examples for each interview question';
