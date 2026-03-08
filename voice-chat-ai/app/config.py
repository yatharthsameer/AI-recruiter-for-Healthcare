"""
Configuration Manager for Enhanced AI Interviewer Bot
Centralizes all environment variable management
"""

import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    url: str
    redis_url: str
    elasticsearch_url: str
    postgres_password: str
    postgres_user: str
    postgres_db: str

@dataclass
class AIConfig:
    """AI model configuration settings"""
    openai_api_key: str
    openai_model: str
    openai_model_tts: str
    openai_transcription_model: str
    openai_tts_voice: str
    model_provider: str
    tts_provider: str

@dataclass
class ScoringConfig:
    """Scoring system configuration"""
    scoring_scale: int
    empathy_bonus_multiplier: float
    patient_story_bonus_multiplier: float
    care_experience_bonus_multiplier: float
    dignity_mention_bonus_multiplier: float
    
    # Question weights
    experience_weight: float
    motivation_weight: float
    punctuality_weight: float
    empathy_weight: float
    communication_weight: float

@dataclass
class TierConfig:
    """Tier classification thresholds"""
    tier_a_plus_score: int
    tier_a_plus_percentile: int
    tier_a_score: int
    tier_a_percentile: int
    tier_a_minus_score: int
    tier_a_minus_percentile: int
    tier_b_plus_score: int
    tier_b_plus_percentile: int

@dataclass
class SystemConfig:
    """System configuration settings"""
    character_name: str
    voice_speed: float
    max_char_length: int
    faster_whisper_local: bool
    debug: bool
    rag_system_enabled: bool
    ml_predictions_enabled: bool
    real_time_rankings_enabled: bool

@dataclass
class VectorDBConfig:
    """Vector database configuration"""
    vector_db_type: str
    elasticsearch_index_name: str
    elasticsearch_timeout: int

@dataclass
class MLConfig:
    """ML model configuration"""
    models_path: str
    retrain_threshold: int
    confidence_threshold: float

@dataclass
class CacheConfig:
    """Cache configuration"""
    redis_cache_ttl: int
    leaderboard_cache_size: int
    ranking_update_interval: int

class ConfigManager:
    """Centralized configuration manager"""
    
    def __init__(self):
        self.database = self._load_database_config()
        self.ai = self._load_ai_config()
        self.scoring = self._load_scoring_config()
        self.tiers = self._load_tier_config()
        self.system = self._load_system_config()
        self.vector_db = self._load_vector_db_config()
        self.ml = self._load_ml_config()
        self.cache = self._load_cache_config()
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment"""
        return DatabaseConfig(
            url=os.getenv('DATABASE_URL', 'postgresql://interview_admin:secure_password@localhost:5432/interview_bot'),
            redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            elasticsearch_url=os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200'),
            postgres_password=os.getenv('POSTGRES_PASSWORD', 'secure_password'),
            postgres_user=os.getenv('POSTGRES_USER', 'interview_admin'),
            postgres_db=os.getenv('POSTGRES_DB', 'interview_bot')
        )
    
    def _load_ai_config(self) -> AIConfig:
        """Load AI model configuration from environment"""
        return AIConfig(
            openai_api_key=os.getenv('OPENAI_API_KEY', ''),
            openai_model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            openai_model_tts=os.getenv('OPENAI_MODEL_TTS', 'gpt-4o-mini-tts'),
            openai_transcription_model=os.getenv('OPENAI_TRANSCRIPTION_MODEL', 'gpt-4o-mini-transcribe'),
            openai_tts_voice=os.getenv('OPENAI_TTS_VOICE', 'alloy'),
            model_provider=os.getenv('MODEL_PROVIDER', 'openai'),
            tts_provider=os.getenv('TTS_PROVIDER', 'openai')
        )
    
    def _load_scoring_config(self) -> ScoringConfig:
        """Load scoring configuration from environment"""
        return ScoringConfig(
            scoring_scale=int(os.getenv('SCORING_SCALE', '100')),
            empathy_bonus_multiplier=float(os.getenv('EMPATHY_BONUS_MULTIPLIER', '1.12')),
            patient_story_bonus_multiplier=float(os.getenv('PATIENT_STORY_BONUS_MULTIPLIER', '1.08')),
            care_experience_bonus_multiplier=float(os.getenv('CARE_EXPERIENCE_BONUS_MULTIPLIER', '1.05')),
            dignity_mention_bonus_multiplier=float(os.getenv('DIGNITY_MENTION_BONUS_MULTIPLIER', '1.05')),
            experience_weight=float(os.getenv('EXPERIENCE_WEIGHT', '0.30')),
            motivation_weight=float(os.getenv('MOTIVATION_WEIGHT', '0.20')),
            punctuality_weight=float(os.getenv('PUNCTUALITY_WEIGHT', '0.15')),
            empathy_weight=float(os.getenv('EMPATHY_WEIGHT', '0.25')),
            communication_weight=float(os.getenv('COMMUNICATION_WEIGHT', '0.10'))
        )
    
    def _load_tier_config(self) -> TierConfig:
        """Load tier configuration from environment"""
        return TierConfig(
            tier_a_plus_score=int(os.getenv('TIER_A_PLUS_SCORE', '90')),
            tier_a_plus_percentile=int(os.getenv('TIER_A_PLUS_PERCENTILE', '95')),
            tier_a_score=int(os.getenv('TIER_A_SCORE', '85')),
            tier_a_percentile=int(os.getenv('TIER_A_PERCENTILE', '85')),
            tier_a_minus_score=int(os.getenv('TIER_A_MINUS_SCORE', '80')),
            tier_a_minus_percentile=int(os.getenv('TIER_A_MINUS_PERCENTILE', '75')),
            tier_b_plus_score=int(os.getenv('TIER_B_PLUS_SCORE', '75')),
            tier_b_plus_percentile=int(os.getenv('TIER_B_PLUS_PERCENTILE', '60'))
        )
    
    def _load_system_config(self) -> SystemConfig:
        """Load system configuration from environment"""
        return SystemConfig(
            character_name=os.getenv('CHARACTER_NAME', 'carebot'),
            voice_speed=float(os.getenv('VOICE_SPEED', '1.0')),
            max_char_length=int(os.getenv('MAX_CHAR_LENGTH', '500')),
            faster_whisper_local=os.getenv('FASTER_WHISPER_LOCAL', 'false').lower() == 'true',
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            rag_system_enabled=os.getenv('RAG_SYSTEM_ENABLED', 'true').lower() == 'true',
            ml_predictions_enabled=os.getenv('ML_PREDICTIONS_ENABLED', 'true').lower() == 'true',
            real_time_rankings_enabled=os.getenv('REAL_TIME_RANKINGS_ENABLED', 'true').lower() == 'true'
        )
    
    def _load_vector_db_config(self) -> VectorDBConfig:
        """Load vector database configuration from environment"""
        return VectorDBConfig(
            vector_db_type=os.getenv('VECTOR_DB_TYPE', 'elasticsearch'),
            elasticsearch_index_name=os.getenv('ELASTICSEARCH_INDEX_NAME', 'caregiver_answers'),
            elasticsearch_timeout=int(os.getenv('ELASTICSEARCH_TIMEOUT', '30'))
        )
    
    def _load_ml_config(self) -> MLConfig:
        """Load ML configuration from environment"""
        return MLConfig(
            models_path=os.getenv('ML_MODELS_PATH', '/app/models'),
            retrain_threshold=int(os.getenv('ML_RETRAIN_THRESHOLD', '20')),
            confidence_threshold=float(os.getenv('ML_CONFIDENCE_THRESHOLD', '0.7'))
        )
    
    def _load_cache_config(self) -> CacheConfig:
        """Load cache configuration from environment"""
        return CacheConfig(
            redis_cache_ttl=int(os.getenv('REDIS_CACHE_TTL', '300')),
            leaderboard_cache_size=int(os.getenv('LEADERBOARD_CACHE_SIZE', '100')),
            ranking_update_interval=int(os.getenv('RANKING_UPDATE_INTERVAL', '60'))
        )
    
    def get_question_weights(self) -> Dict[str, float]:
        """Get question dimension weights as dictionary"""
        return {
            'experience': self.scoring.experience_weight,
            'motivation': self.scoring.motivation_weight,
            'punctuality': self.scoring.punctuality_weight,
            'empathy': self.scoring.empathy_weight,
            'communication': self.scoring.communication_weight
        }
    
    def get_caregiver_bonuses(self) -> Dict[str, float]:
        """Get caregiver bonus multipliers as dictionary"""
        return {
            'empathy_bonus': self.scoring.empathy_bonus_multiplier,
            'patient_story_bonus': self.scoring.patient_story_bonus_multiplier,
            'care_experience_bonus': self.scoring.care_experience_bonus_multiplier,
            'dignity_mention_bonus': self.scoring.dignity_mention_bonus_multiplier
        }
    
    def get_tier_thresholds(self) -> Dict[str, Dict[str, int]]:
        """Get tier thresholds as dictionary"""
        return {
            'A+': {
                'score': self.tiers.tier_a_plus_score,
                'percentile': self.tiers.tier_a_plus_percentile
            },
            'A': {
                'score': self.tiers.tier_a_score,
                'percentile': self.tiers.tier_a_percentile
            },
            'A-': {
                'score': self.tiers.tier_a_minus_score,
                'percentile': self.tiers.tier_a_minus_percentile
            },
            'B+': {
                'score': self.tiers.tier_b_plus_score,
                'percentile': self.tiers.tier_b_plus_percentile
            }
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration and return status"""
        issues = []
        
        # Check required API keys
        if not self.ai.openai_api_key:
            issues.append("OPENAI_API_KEY is required")
        
        # Check question weights sum to 1.0
        total_weight = sum(self.get_question_weights().values())
        if abs(total_weight - 1.0) > 0.01:
            issues.append(f"Question weights sum to {total_weight}, should be 1.0")
        
        # Check database URLs
        if not self.database.url.startswith('postgresql://'):
            issues.append("DATABASE_URL should start with postgresql://")
        
        if not self.database.redis_url.startswith('redis://'):
            issues.append("REDIS_URL should start with redis://")
        
        if not self.database.elasticsearch_url.startswith('http'):
            issues.append("ELASTICSEARCH_URL should start with http://")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'config_summary': {
                'database_url': self.database.url,
                'redis_url': self.database.redis_url,
                'elasticsearch_url': self.database.elasticsearch_url,
                'model_provider': self.ai.model_provider,
                'scoring_scale': self.scoring.scoring_scale,
                'question_weights': self.get_question_weights(),
                'tier_thresholds': self.get_tier_thresholds()
            }
        }
    
    def export_config(self) -> str:
        """Export current configuration as environment file format"""
        config_lines = [
            "# Enhanced AI Interviewer Bot Configuration",
            "# Auto-generated configuration file",
            "",
            "# Database Configuration",
            f"DATABASE_URL={self.database.url}",
            f"REDIS_URL={self.database.redis_url}",
            f"ELASTICSEARCH_URL={self.database.elasticsearch_url}",
            f"POSTGRES_PASSWORD={self.database.postgres_password}",
            f"POSTGRES_USER={self.database.postgres_user}",
            f"POSTGRES_DB={self.database.postgres_db}",
            "",
            "# OpenAI Configuration",
            f"OPENAI_API_KEY={self.ai.openai_api_key}",
            f"OPENAI_MODEL={self.ai.openai_model}",
            f"OPENAI_MODEL_TTS={self.ai.openai_model_tts}",
            f"OPENAI_TRANSCRIPTION_MODEL={self.ai.openai_transcription_model}",
            f"OPENAI_TTS_VOICE={self.ai.openai_tts_voice}",
            "",
            "# Model Provider",
            f"MODEL_PROVIDER={self.ai.model_provider}",
            f"TTS_PROVIDER={self.ai.tts_provider}",
            "",
            "# Character Configuration", 
            f"CHARACTER_NAME={self.system.character_name}",
            "",
            "# Voice Configuration",
            f"VOICE_SPEED={self.system.voice_speed}",
            f"MAX_CHAR_LENGTH={self.system.max_char_length}",
            "",
            "# System Configuration",
            f"FASTER_WHISPER_LOCAL={str(self.system.faster_whisper_local).lower()}",
            f"DEBUG={str(self.system.debug).lower()}",
            "",
            "# Enhanced System Configuration",
            f"RAG_SYSTEM_ENABLED={str(self.system.rag_system_enabled).lower()}",
            f"ML_PREDICTIONS_ENABLED={str(self.system.ml_predictions_enabled).lower()}",
            f"REAL_TIME_RANKINGS_ENABLED={str(self.system.real_time_rankings_enabled).lower()}",
            "",
            "# Vector Database Configuration",
            f"VECTOR_DB_TYPE={self.vector_db.vector_db_type}",
            f"ELASTICSEARCH_INDEX_NAME={self.vector_db.elasticsearch_index_name}",
            f"ELASTICSEARCH_TIMEOUT={self.vector_db.elasticsearch_timeout}",
            "",
            "# ML Model Configuration",
            f"ML_MODELS_PATH={self.ml.models_path}",
            f"ML_RETRAIN_THRESHOLD={self.ml.retrain_threshold}",
            f"ML_CONFIDENCE_THRESHOLD={self.ml.confidence_threshold}",
            "",
            "# Scoring Configuration",
            f"SCORING_SCALE={self.scoring.scoring_scale}",
            f"EMPATHY_BONUS_MULTIPLIER={self.scoring.empathy_bonus_multiplier}",
            f"PATIENT_STORY_BONUS_MULTIPLIER={self.scoring.patient_story_bonus_multiplier}",
            f"CARE_EXPERIENCE_BONUS_MULTIPLIER={self.scoring.care_experience_bonus_multiplier}",
            f"DIGNITY_MENTION_BONUS_MULTIPLIER={self.scoring.dignity_mention_bonus_multiplier}",
            "",
            "# Question Weights",
            f"EXPERIENCE_WEIGHT={self.scoring.experience_weight}",
            f"MOTIVATION_WEIGHT={self.scoring.motivation_weight}",
            f"PUNCTUALITY_WEIGHT={self.scoring.punctuality_weight}",
            f"EMPATHY_WEIGHT={self.scoring.empathy_weight}",
            f"COMMUNICATION_WEIGHT={self.scoring.communication_weight}",
            "",
            "# Tier Thresholds",
            f"TIER_A_PLUS_SCORE={self.tiers.tier_a_plus_score}",
            f"TIER_A_PLUS_PERCENTILE={self.tiers.tier_a_plus_percentile}",
            f"TIER_A_SCORE={self.tiers.tier_a_score}",
            f"TIER_A_PERCENTILE={self.tiers.tier_a_percentile}",
            f"TIER_A_MINUS_SCORE={self.tiers.tier_a_minus_score}",
            f"TIER_A_MINUS_PERCENTILE={self.tiers.tier_a_minus_percentile}",
            f"TIER_B_PLUS_SCORE={self.tiers.tier_b_plus_score}",
            f"TIER_B_PLUS_PERCENTILE={self.tiers.tier_b_plus_percentile}",
            "",
            "# Cache Configuration",
            f"REDIS_CACHE_TTL={self.cache.redis_cache_ttl}",
            f"LEADERBOARD_CACHE_SIZE={self.cache.leaderboard_cache_size}",
            f"RANKING_UPDATE_INTERVAL={self.cache.ranking_update_interval}"
        ]
        
        return "\n".join(config_lines)

# Global configuration instance
config = ConfigManager()

# Convenience functions for accessing configuration
def get_database_url() -> str:
    return config.database.url

def get_redis_url() -> str:
    return config.database.redis_url

def get_elasticsearch_url() -> str:
    return config.database.elasticsearch_url

def get_question_weights() -> Dict[str, float]:
    return config.get_question_weights()

def get_caregiver_bonuses() -> Dict[str, float]:
    return config.get_caregiver_bonuses()

def get_tier_thresholds() -> Dict[str, Dict[str, int]]:
    return config.get_tier_thresholds()

def is_rag_enabled() -> bool:
    return config.system.rag_system_enabled

def is_ml_enabled() -> bool:
    return config.system.ml_predictions_enabled

def is_rankings_enabled() -> bool:
    return config.system.real_time_rankings_enabled

# Example usage
if __name__ == "__main__":
    # Validate configuration
    validation = config.validate_configuration()
    
    if validation['valid']:
        print("✅ Configuration is valid")
        print("📊 Configuration Summary:")
        for key, value in validation['config_summary'].items():
            print(f"  {key}: {value}")
    else:
        print("❌ Configuration issues found:")
        for issue in validation['issues']:
            print(f"  - {issue}")
    
    # Export configuration
    print("\n📄 Current Configuration:")
    print(config.export_config())
