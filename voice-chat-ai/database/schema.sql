-- Enhanced AI Interviewer Bot Database Schema
-- PostgreSQL database for caregiver interview system with RAG integration

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core candidate information
CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    caregiving_experience BOOLEAN DEFAULT FALSE,
    has_per_id BOOLEAN DEFAULT FALSE,
    drivers_license BOOLEAN DEFAULT FALSE,
    auto_insurance BOOLEAN DEFAULT FALSE,
    availability JSONB, -- ["Morning", "Afternoon", "Evening"]
    weekly_hours INTEGER,
    languages JSONB, -- ["English", "Spanish"]
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB -- Additional candidate info
);

-- Interview sessions
CREATE TABLE interview_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    session_status VARCHAR(20) DEFAULT 'in_progress',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    total_score DECIMAL(5,2), -- Out of 100
    recommendation VARCHAR(20), -- 'hire', 'consider', 'reject'
    
    -- Dimension scores (out of 100)
    experience_avg DECIMAL(5,2),
    motivation_score DECIMAL(5,2),
    punctuality_avg DECIMAL(5,2),
    empathy_avg DECIMAL(5,2),
    communication_score DECIMAL(5,2),
    
    -- Audio metadata
    audio_filename VARCHAR(255),
    audio_filepath VARCHAR(500),
    file_size BIGINT,
    content_type VARCHAR(100),
    
    metadata JSONB
);

-- Individual question responses with RAG scores
CREATE TABLE question_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    question_id VARCHAR(50) NOT NULL, -- Q1, Q2, Q3, etc.
    question_text TEXT NOT NULL,
    candidate_answer TEXT NOT NULL,
    transcription_confidence DECIMAL(3,2),
    
    -- Multi-dimensional scores (out of 100)
    semantic_similarity_score DECIMAL(5,2), -- RAG-based score
    completeness_score DECIMAL(5,2),
    empathy_score DECIMAL(5,2), -- Caregiver-specific
    behavioral_score DECIMAL(5,2),
    
    -- RAG metadata
    rag_best_match_score DECIMAL(3,2), -- 0.89 = 89% similarity
    rag_match_quality VARCHAR(20), -- 'excellent', 'good', 'fair', 'poor'
    expected_answer_id VARCHAR(50), -- Reference to matched answer
    
    -- Caregiver contextual adjustments
    empathy_bonus DECIMAL(3,2) DEFAULT 1.0,
    patient_story_bonus DECIMAL(3,2) DEFAULT 1.0,
    care_experience_bonus DECIMAL(3,2) DEFAULT 1.0,
    dignity_mention_bonus DECIMAL(3,2) DEFAULT 1.0,
    
    final_question_score DECIMAL(5,2), -- Final adjusted score
    created_at TIMESTAMP DEFAULT NOW()
);

-- Real-time candidate rankings
CREATE TABLE candidate_rankings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    overall_rank INTEGER NOT NULL,
    percentile_rank DECIMAL(5,2), -- 85.3 = 85.3rd percentile
    tier VARCHAR(5) NOT NULL, -- A+, A, A-, B+, B, B-, C
    
    -- Detailed scores (out of 100)
    experience_avg DECIMAL(5,2),
    motivation_score DECIMAL(5,2),
    punctuality_avg DECIMAL(5,2),
    empathy_avg DECIMAL(5,2),
    communication_score DECIMAL(5,2),
    
    total_weighted_score DECIMAL(5,2),
    
    -- Comparative metrics
    cohort_percentile DECIMAL(5,2), -- Within similar candidates
    similar_candidates_count INTEGER,
    
    -- ML predictions
    hiring_probability DECIMAL(3,2), -- 0.85 = 85%
    expected_performance DECIMAL(5,2), -- Expected rating /100
    risk_factors JSONB, -- ["reliability_concerns", "limited_experience"]
    confidence_level VARCHAR(20), -- 'high', 'medium', 'low'
    
    last_updated TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(candidate_id) -- One ranking per candidate
);

-- Expected answers for RAG comparison
CREATE TABLE expected_answers (
    id VARCHAR(50) PRIMARY KEY,
    question_id VARCHAR(50) NOT NULL, -- Q1, Q2, Q3, etc.
    answer_text TEXT NOT NULL,
    quality_level VARCHAR(20) NOT NULL, -- 'excellent', 'good', 'fair', 'poor'
    score_range_min INTEGER, -- 85 for excellent
    score_range_max INTEGER, -- 100 for excellent
    
    -- Caregiver-specific attributes
    empathy_indicators JSONB, -- ["patience", "dignity", "understanding"]
    experience_indicators JSONB, -- ["specific_examples", "skill_transfer"]
    behavioral_patterns JSONB, -- ["STAR_method", "problem_solving"]
    
    -- Vector embedding reference
    embedding_id VARCHAR(100), -- Reference to vector database
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Evaluation history for ML training
CREATE TABLE evaluation_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID REFERENCES candidates(id),
    interview_score DECIMAL(5,2),
    hired BOOLEAN,
    hiring_date DATE,
    performance_rating DECIMAL(5,2), -- 6-month performance review
    retention_months INTEGER, -- How long they stayed
    supervisor_feedback TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- System configuration
CREATE TABLE system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_candidates_email ON candidates(email);
CREATE INDEX idx_candidates_created_at ON candidates(created_at);

CREATE INDEX idx_interview_sessions_candidate ON interview_sessions(candidate_id);
CREATE INDEX idx_interview_sessions_status ON interview_sessions(session_status);
CREATE INDEX idx_interview_sessions_completed ON interview_sessions(completed_at) WHERE session_status = 'completed';

CREATE INDEX idx_question_responses_session ON question_responses(session_id);
CREATE INDEX idx_question_responses_question_id ON question_responses(question_id);
CREATE INDEX idx_question_responses_rag_score ON question_responses(rag_best_match_score DESC);
CREATE INDEX idx_question_responses_final_score ON question_responses(final_question_score DESC);

CREATE INDEX idx_candidate_rankings_rank ON candidate_rankings(overall_rank);
CREATE INDEX idx_candidate_rankings_tier ON candidate_rankings(tier);
CREATE INDEX idx_candidate_rankings_score ON candidate_rankings(total_weighted_score DESC);
CREATE INDEX idx_candidate_rankings_percentile ON candidate_rankings(percentile_rank DESC);

CREATE INDEX idx_expected_answers_question ON expected_answers(question_id);
CREATE INDEX idx_expected_answers_quality ON expected_answers(quality_level);

CREATE INDEX idx_evaluation_history_candidate ON evaluation_history(candidate_id);
CREATE INDEX idx_evaluation_history_hired ON evaluation_history(hired);

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_candidates_updated_at BEFORE UPDATE ON candidates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, description) VALUES
('question_weights', '{"experience": 0.30, "motivation": 0.20, "punctuality": 0.15, "empathy": 0.25, "communication": 0.10}', 'Weights for calculating final scores'),
('tier_thresholds', '{"A+": {"score": 90, "percentile": 95}, "A": {"score": 85, "percentile": 85}, "A-": {"score": 80, "percentile": 75}, "B+": {"score": 75, "percentile": 60}, "B": {"score": 70, "percentile": 40}, "B-": {"score": 65, "percentile": 25}}', 'Thresholds for tier classification'),
('caregiver_bonuses', '{"empathy_bonus": 1.12, "patient_story_bonus": 1.08, "care_experience_bonus": 1.05, "dignity_mention_bonus": 1.05}', 'Contextual bonus multipliers for caregiver responses');

-- Sample expected answers for RAG system
INSERT INTO expected_answers VALUES
('Q1_excellent_001', 'Q1', 'I worked as a certified nursing assistant for 3 years at Sunrise Senior Living. I cared for residents with various conditions including dementia, diabetes, and mobility issues. My daily responsibilities included assisting with personal care, medication reminders, meal assistance, and providing emotional support. I helped with transfers using proper body mechanics and gait belts, and I was trained in infection control protocols. What I found most rewarding was building relationships with residents and seeing how small acts of kindness could brighten their day.', 'excellent', 90, 100, 
'["compassion", "professional_experience", "specific_examples", "relationship_building"]', 
'["CNA_certification", "3_years_experience", "diverse_conditions", "technical_skills"]', 
'["situation_described", "tasks_detailed", "actions_specific", "results_meaningful"]', 
'q1_exc_001_embedding'),

('Q7_excellent_001', 'Q7', 'I cared for my grandmother with dementia for two years after she moved in with us. The most difficult part was watching her confusion and frustration, especially during sundowning episodes. She would sometimes not recognize me or become agitated. I learned to stay calm, use simple words, and redirect her attention to activities she enjoyed like looking at old photos. The most meaningful part was realizing that even though her memory was fading, her emotions and need for connection remained. When I played her favorite music or held her hand, I could see glimpses of the grandmother I knew. It taught me that dignity and respect are crucial in caregiving, and that the person is still there even when the disease progresses.', 'excellent', 90, 100,
'["patience", "dignity", "emotional_intelligence", "person_centered_care", "understanding"]',
'["2_years_experience", "dementia_care", "behavioral_management", "adaptive_strategies"]',
'["situation_personal", "challenges_acknowledged", "actions_compassionate", "learning_demonstrated"]',
'q7_exc_001_embedding');
