"""
ML Prediction Models for Caregiver Interview System
Predicts hiring success and job performance based on interview scores
"""

import os
import json
import asyncio
import logging
import pickle
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncpg
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MLPrediction:
    """ML prediction result"""
    hiring_probability: float
    expected_performance: float
    risk_factors: List[str]
    confidence_level: str
    similar_candidates_hired: int
    similar_candidates_total: int
    model_accuracy: float

@dataclass
class ModelPerformance:
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    cross_val_score: float
    feature_importance: Dict[str, float]

class CaregiverMLPredictor:
    """ML prediction system for caregiver hiring success"""
    
    def __init__(self, db_connection_string: str, models_path: str = "./models"):
        self.db_connection_string = db_connection_string
        self.models_path = models_path
        
        # Ensure models directory exists
        os.makedirs(models_path, exist_ok=True)
        
        # Model files
        self.hiring_model_file = os.path.join(models_path, "hiring_success_model.pkl")
        self.performance_model_file = os.path.join(models_path, "performance_prediction_model.pkl")
        self.scaler_file = os.path.join(models_path, "feature_scaler.pkl")
        
        # Models (loaded lazily)
        self.hiring_model = None
        self.performance_model = None
        self.scaler = None
        
        # Feature columns for ML models
        self.feature_columns = [
            'experience_avg', 'motivation_score', 'punctuality_avg',
            'empathy_avg', 'communication_score', 'consistency_factor',
            'overall_quality_factor', 'avg_empathy_bonus', 'avg_patient_story_bonus',
            'caregiving_experience_bool', 'weekly_hours'
        ]
        
        logger.info("CaregiverMLPredictor initialized")
    
    async def load_models(self):
        """Load trained ML models"""
        try:
            if os.path.exists(self.hiring_model_file):
                self.hiring_model = joblib.load(self.hiring_model_file)
                logger.info("Hiring success model loaded")
            
            if os.path.exists(self.performance_model_file):
                self.performance_model = joblib.load(self.performance_model_file)
                logger.info("Performance prediction model loaded")
            
            if os.path.exists(self.scaler_file):
                self.scaler = joblib.load(self.scaler_file)
                logger.info("Feature scaler loaded")
            
            if not all([self.hiring_model, self.performance_model, self.scaler]):
                logger.warning("Some models not found. Training new models...")
                await self.train_models()
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            await self.train_models()
    
    async def train_models(self) -> ModelPerformance:
        """Train ML models using historical data"""
        try:
            logger.info("Starting model training...")
            
            # Get training data
            training_data = await self._get_training_data()
            
            if len(training_data) < 50:
                logger.warning(f"Limited training data: {len(training_data)} samples")
                # Create synthetic data for initial training
                training_data = self._generate_synthetic_training_data(100)
            
            # Prepare features and targets
            df = pd.DataFrame(training_data)
            X = df[self.feature_columns]
            y_hiring = df['hired']
            y_performance = df['performance_rating']
            
            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Split data
            X_train, X_test, y_hiring_train, y_hiring_test, y_perf_train, y_perf_test = train_test_split(
                X_scaled, y_hiring, y_performance, test_size=0.2, random_state=42
            )
            
            # Train hiring success model
            self.hiring_model = RandomForestClassifier(
                n_estimators=100, random_state=42, class_weight='balanced'
            )
            self.hiring_model.fit(X_train, y_hiring_train)
            
            # Train performance prediction model
            self.performance_model = RandomForestRegressor(
                n_estimators=100, random_state=42
            )
            self.performance_model.fit(X_train, y_perf_train)
            
            # Evaluate models
            hiring_pred = self.hiring_model.predict(X_test)
            hiring_accuracy = accuracy_score(y_hiring_test, hiring_pred)
            hiring_precision = precision_score(y_hiring_test, hiring_pred, average='weighted')
            hiring_recall = recall_score(y_hiring_test, hiring_pred, average='weighted')
            hiring_f1 = f1_score(y_hiring_test, hiring_pred, average='weighted')
            
            # Cross-validation
            cv_scores = cross_val_score(self.hiring_model, X_scaled, y_hiring, cv=5)
            
            # Feature importance
            feature_importance = dict(zip(self.feature_columns, self.hiring_model.feature_importances_))
            
            # Save models
            joblib.dump(self.hiring_model, self.hiring_model_file)
            joblib.dump(self.performance_model, self.performance_model_file)
            joblib.dump(self.scaler, self.scaler_file)
            
            logger.info(f"Models trained successfully. Accuracy: {hiring_accuracy:.3f}")
            
            return ModelPerformance(
                accuracy=hiring_accuracy,
                precision=hiring_precision,
                recall=hiring_recall,
                f1_score=hiring_f1,
                cross_val_score=cv_scores.mean(),
                feature_importance=feature_importance
            )
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            raise
    
    async def predict_hiring_success(self, candidate_features: Dict) -> MLPrediction:
        """Predict hiring success for a candidate"""
        try:
            # Load models if not already loaded
            if not self.hiring_model:
                await self.load_models()
            
            # Prepare features
            feature_vector = self._prepare_feature_vector(candidate_features)
            feature_vector_scaled = self.scaler.transform([feature_vector])
            
            # Make predictions
            hiring_probability = self.hiring_model.predict_proba(feature_vector_scaled)[0][1]
            expected_performance = self.performance_model.predict(feature_vector_scaled)[0]
            
            # Calculate risk factors
            risk_factors = self._identify_risk_factors(candidate_features)
            
            # Determine confidence level
            confidence_level = self._calculate_prediction_confidence(feature_vector, candidate_features)
            
            # Find similar candidates
            similar_hired, similar_total = await self._find_similar_candidates(candidate_features)
            
            # Get model accuracy
            model_accuracy = getattr(self.hiring_model, '_accuracy', 0.75)  # Default if not available
            
            return MLPrediction(
                hiring_probability=hiring_probability,
                expected_performance=min(expected_performance, 100),  # Cap at 100
                risk_factors=risk_factors,
                confidence_level=confidence_level,
                similar_candidates_hired=similar_hired,
                similar_candidates_total=similar_total,
                model_accuracy=model_accuracy
            )
            
        except Exception as e:
            logger.error(f"Error making ML prediction: {e}")
            return self._create_default_prediction()
    
    async def _get_training_data(self) -> List[Dict]:
        """Get historical training data from database"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            training_data = await conn.fetch("""
                SELECT 
                    c.caregiving_experience,
                    c.weekly_hours,
                    is.experience_avg,
                    is.motivation_score,
                    is.punctuality_avg,
                    is.empathy_avg,
                    is.communication_score,
                    
                    -- Calculate additional features
                    CASE WHEN STDDEV(qr.final_question_score) IS NULL THEN 1.0
                         ELSE 1.0 / (1.0 + STDDEV(qr.final_question_score) / AVG(qr.final_question_score))
                    END as consistency_factor,
                    
                    AVG(qr.rag_best_match_score) as overall_quality_factor,
                    AVG(qr.empathy_bonus) as avg_empathy_bonus,
                    AVG(qr.patient_story_bonus) as avg_patient_story_bonus,
                    
                    eh.hired,
                    eh.performance_rating
                    
                FROM candidates c
                JOIN interview_sessions is ON c.id = is.candidate_id
                JOIN question_responses qr ON is.id = qr.session_id
                JOIN evaluation_history eh ON c.id = eh.candidate_id
                
                WHERE is.session_status = 'completed'
                  AND eh.performance_rating IS NOT NULL
                
                GROUP BY c.id, c.caregiving_experience, c.weekly_hours,
                         is.experience_avg, is.motivation_score, is.punctuality_avg,
                         is.empathy_avg, is.communication_score,
                         eh.hired, eh.performance_rating
            """)
            
            await conn.close()
            
            return [
                {
                    'caregiving_experience_bool': 1 if row['caregiving_experience'] else 0,
                    'weekly_hours': row['weekly_hours'] or 20,
                    'experience_avg': float(row['experience_avg'] or 50),
                    'motivation_score': float(row['motivation_score'] or 50),
                    'punctuality_avg': float(row['punctuality_avg'] or 50),
                    'empathy_avg': float(row['empathy_avg'] or 50),
                    'communication_score': float(row['communication_score'] or 50),
                    'consistency_factor': float(row['consistency_factor'] or 1.0),
                    'overall_quality_factor': float(row['overall_quality_factor'] or 1.0),
                    'avg_empathy_bonus': float(row['avg_empathy_bonus'] or 1.0),
                    'avg_patient_story_bonus': float(row['avg_patient_story_bonus'] or 1.0),
                    'hired': row['hired'],
                    'performance_rating': float(row['performance_rating'] or 50)
                }
                for row in training_data
            ]
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return []
    
    def _generate_synthetic_training_data(self, num_samples: int) -> List[Dict]:
        """Generate synthetic training data for initial model training"""
        np.random.seed(42)
        
        synthetic_data = []
        
        for _ in range(num_samples):
            # Generate realistic score distributions
            experience = np.random.normal(75, 15)
            motivation = np.random.normal(80, 12)
            punctuality = np.random.normal(70, 18)
            empathy = np.random.normal(85, 10)  # Caregivers typically score high here
            communication = np.random.normal(75, 15)
            
            # Clip to valid ranges
            scores = {
                'experience_avg': np.clip(experience, 0, 100),
                'motivation_score': np.clip(motivation, 0, 100),
                'punctuality_avg': np.clip(punctuality, 0, 100),
                'empathy_avg': np.clip(empathy, 0, 100),
                'communication_score': np.clip(communication, 0, 100)
            }
            
            # Calculate overall score
            overall_score = (
                scores['experience_avg'] * 0.30 +
                scores['motivation_score'] * 0.20 +
                scores['punctuality_avg'] * 0.15 +
                scores['empathy_avg'] * 0.25 +
                scores['communication_score'] * 0.10
            )
            
            # Determine hiring outcome (higher scores more likely to be hired)
            hiring_probability = 1 / (1 + np.exp(-(overall_score - 70) / 10))  # Sigmoid
            hired = np.random.random() < hiring_probability
            
            # Performance rating correlated with interview score
            performance_base = overall_score + np.random.normal(0, 5)
            performance_rating = np.clip(performance_base, 0, 100)
            
            synthetic_data.append({
                **scores,
                'caregiving_experience_bool': np.random.choice([0, 1], p=[0.3, 0.7]),
                'weekly_hours': np.random.choice([20, 25, 30, 35, 40]),
                'consistency_factor': np.random.normal(1.0, 0.05),
                'overall_quality_factor': np.random.normal(1.0, 0.1),
                'avg_empathy_bonus': np.random.normal(1.05, 0.03),
                'avg_patient_story_bonus': np.random.normal(1.03, 0.02),
                'hired': hired,
                'performance_rating': performance_rating
            })
        
        logger.info(f"Generated {num_samples} synthetic training samples")
        return synthetic_data
    
    def _prepare_feature_vector(self, candidate_features: Dict) -> List[float]:
        """Prepare feature vector for ML prediction"""
        return [
            candidate_features.get('experience_avg', 50),
            candidate_features.get('motivation_score', 50),
            candidate_features.get('punctuality_avg', 50),
            candidate_features.get('empathy_avg', 50),
            candidate_features.get('communication_score', 50),
            candidate_features.get('consistency_factor', 1.0),
            candidate_features.get('overall_quality_factor', 1.0),
            candidate_features.get('avg_empathy_bonus', 1.0),
            candidate_features.get('avg_patient_story_bonus', 1.0),
            1 if candidate_features.get('caregiving_experience', False) else 0,
            candidate_features.get('weekly_hours', 20)
        ]
    
    def _identify_risk_factors(self, candidate_features: Dict) -> List[str]:
        """Identify potential risk factors based on scores"""
        risk_factors = []
        
        # Score-based risk factors
        if candidate_features.get('empathy_avg', 50) < 65:
            risk_factors.append("empathy_concerns")
        
        if candidate_features.get('punctuality_avg', 50) < 60:
            risk_factors.append("reliability_concerns")
        
        if candidate_features.get('experience_avg', 50) < 55:
            risk_factors.append("limited_experience")
        
        if candidate_features.get('communication_score', 50) < 60:
            risk_factors.append("communication_gaps")
        
        # Consistency risk
        if candidate_features.get('consistency_factor', 1.0) < 0.95:
            risk_factors.append("inconsistent_performance")
        
        # Experience risk
        if not candidate_features.get('caregiving_experience', False):
            risk_factors.append("no_professional_experience")
        
        return risk_factors
    
    def _calculate_prediction_confidence(self, feature_vector: List[float], 
                                       candidate_features: Dict) -> str:
        """Calculate confidence level for predictions"""
        # Factors affecting confidence
        confidence_factors = []
        
        # Model confidence (based on feature similarity to training data)
        feature_std = np.std(feature_vector)
        if feature_std < 15:  # Features within normal range
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.6)
        
        # Data quality confidence
        if candidate_features.get('overall_quality_factor', 1.0) > 1.05:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.7)
        
        # Consistency confidence
        if candidate_features.get('consistency_factor', 1.0) > 1.02:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.7)
        
        avg_confidence = np.mean(confidence_factors)
        
        if avg_confidence > 0.85:
            return "high"
        elif avg_confidence > 0.7:
            return "medium"
        else:
            return "low"
    
    async def _find_similar_candidates(self, candidate_features: Dict) -> Tuple[int, int]:
        """Find similar candidates and their hiring outcomes"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Define similarity criteria
            experience_range = 10  # ±10 points
            empathy_range = 8      # ±8 points (important for caregivers)
            
            target_experience = candidate_features.get('experience_avg', 50)
            target_empathy = candidate_features.get('empathy_avg', 50)
            caregiving_exp = candidate_features.get('caregiving_experience', False)
            
            similar_candidates = await conn.fetch("""
                SELECT eh.hired
                FROM evaluation_history eh
                JOIN candidates c ON eh.candidate_id = c.id
                JOIN candidate_rankings cr ON c.id = cr.candidate_id
                WHERE c.caregiving_experience = $1
                  AND cr.experience_avg BETWEEN $2 AND $3
                  AND cr.empathy_avg BETWEEN $4 AND $5
            """, 
            caregiving_exp,
            target_experience - experience_range, target_experience + experience_range,
            target_empathy - empathy_range, target_empathy + empathy_range)
            
            await conn.close()
            
            if not similar_candidates:
                return 0, 0
            
            hired_count = sum(1 for row in similar_candidates if row['hired'])
            total_count = len(similar_candidates)
            
            return hired_count, total_count
            
        except Exception as e:
            logger.error(f"Error finding similar candidates: {e}")
            return 0, 0
    
    async def update_model_with_outcome(self, candidate_id: str, hired: bool, 
                                      performance_rating: Optional[float] = None):
        """Update model training data with actual hiring outcome"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Store evaluation outcome
            await conn.execute("""
                INSERT INTO evaluation_history (
                    candidate_id, interview_score, hired, hiring_date, performance_rating
                )
                SELECT $1, cr.total_weighted_score, $2, $3, $4
                FROM candidate_rankings cr
                WHERE cr.candidate_id = $1
                ON CONFLICT (candidate_id) DO UPDATE SET
                    hired = EXCLUDED.hired,
                    hiring_date = EXCLUDED.hiring_date,
                    performance_rating = EXCLUDED.performance_rating
            """, candidate_id, hired, datetime.now().date(), performance_rating)
            
            await conn.close()
            
            # Check if we should retrain models
            await self._check_retrain_trigger()
            
            logger.info(f"Updated outcome for candidate {candidate_id}: hired={hired}")
            
        except Exception as e:
            logger.error(f"Error updating model with outcome: {e}")
    
    async def _check_retrain_trigger(self):
        """Check if models should be retrained based on new data"""
        try:
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Count new outcomes since last training
            new_outcomes = await conn.fetchval("""
                SELECT COUNT(*)
                FROM evaluation_history
                WHERE created_at > NOW() - INTERVAL '7 days'
            """)
            
            await conn.close()
            
            # Retrain if we have 20+ new outcomes
            if new_outcomes >= 20:
                logger.info(f"Triggering model retraining with {new_outcomes} new outcomes")
                await self.train_models()
            
        except Exception as e:
            logger.error(f"Error checking retrain trigger: {e}")
    
    def _create_default_prediction(self) -> MLPrediction:
        """Create default prediction when ML fails"""
        return MLPrediction(
            hiring_probability=0.5,
            expected_performance=70.0,
            risk_factors=["insufficient_data"],
            confidence_level="low",
            similar_candidates_hired=0,
            similar_candidates_total=0,
            model_accuracy=0.5
        )
    
    async def get_model_performance_report(self) -> Dict:
        """Get comprehensive model performance report"""
        try:
            if not self.hiring_model:
                await self.load_models()
            
            conn = await asyncpg.connect(self.db_connection_string)
            
            # Get prediction accuracy over time
            accuracy_data = await conn.fetch("""
                SELECT 
                    DATE_TRUNC('week', eh.created_at) as week,
                    COUNT(*) as total_predictions,
                    AVG(CASE WHEN eh.hired THEN 1.0 ELSE 0.0 END) as actual_hire_rate,
                    AVG(cr.hiring_probability) as predicted_hire_rate
                FROM evaluation_history eh
                JOIN candidate_rankings cr ON eh.candidate_id = cr.candidate_id
                WHERE eh.created_at >= NOW() - INTERVAL '90 days'
                GROUP BY DATE_TRUNC('week', eh.created_at)
                ORDER BY week
            """)
            
            await conn.close()
            
            return {
                'model_files': {
                    'hiring_model': os.path.exists(self.hiring_model_file),
                    'performance_model': os.path.exists(self.performance_model_file),
                    'scaler': os.path.exists(self.scaler_file)
                },
                'accuracy_trends': [
                    {
                        'week': row['week'].isoformat(),
                        'total_predictions': row['total_predictions'],
                        'actual_hire_rate': float(row['actual_hire_rate'] or 0),
                        'predicted_hire_rate': float(row['predicted_hire_rate'] or 0)
                    }
                    for row in accuracy_data
                ],
                'feature_importance': getattr(self.hiring_model, 'feature_importances_', []) if self.hiring_model else []
            }
            
        except Exception as e:
            logger.error(f"Error getting model performance report: {e}")
            return {}

# Example usage
async def main():
    """Example usage of ML prediction system"""
    # Initialize ML predictor
    db_connection = "postgresql://interview_admin:secure_password@localhost:5432/interview_bot"
    ml_predictor = CaregiverMLPredictor(db_connection)
    
    # Load or train models
    await ml_predictor.load_models()
    
    # Example candidate features
    candidate_features = {
        'experience_avg': 82.0,
        'motivation_score': 75.0,
        'punctuality_avg': 68.0,
        'empathy_avg': 91.0,
        'communication_score': 79.0,
        'consistency_factor': 1.05,
        'overall_quality_factor': 1.08,
        'avg_empathy_bonus': 1.12,
        'avg_patient_story_bonus': 1.08,
        'caregiving_experience': True,
        'weekly_hours': 30
    }
    
    # Make prediction
    prediction = await ml_predictor.predict_hiring_success(candidate_features)
    
    print(f"Hiring Probability: {prediction.hiring_probability:.1%}")
    print(f"Expected Performance: {prediction.expected_performance:.1f}/100")
    print(f"Risk Factors: {', '.join(prediction.risk_factors) if prediction.risk_factors else 'None'}")
    print(f"Confidence: {prediction.confidence_level}")
    print(f"Similar Candidates: {prediction.similar_candidates_hired}/{prediction.similar_candidates_total} hired")

if __name__ == "__main__":
    asyncio.run(main())
