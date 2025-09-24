"""
Learning Engine for Heisha Weather Prediction Control
Machine learning algorithms for adaptive heat pump control
"""

import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
import pandas as pd


class LearningEngine:
    """Learning engine for adaptive heat pump control"""
    
    def __init__(self, config: Dict[str, Any], data_path: str = "/data/learning_data.json"):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.data_path = Path(data_path)
        
        # Learning parameters
        self.learning_rate = config['advanced']['learning_rate']
        self.max_data_age_days = 365  # Keep data for 1 year
        self.min_samples_for_learning = 100
        
        # Data storage
        self.historical_data = []
        self.models = {}
        self.scalers = {}
        self.model_accuracy = {}
        
        # Initialize models
        self._initialize_models()
        
        # Load existing data
        self._load_data()
    
    def _initialize_models(self):
        """Initialize machine learning models"""
        model_params = {
            'n_estimators': 50,
            'max_depth': 10,
            'random_state': 42,
            'n_jobs': -1
        }
        
        # Model for predicting temperature response
        self.models['temperature_response'] = RandomForestRegressor(**model_params)
        self.scalers['temperature_response'] = StandardScaler()
        
        # Model for predicting energy consumption
        self.models['energy_consumption'] = RandomForestRegressor(**model_params)
        self.scalers['energy_consumption'] = StandardScaler()
        
        # Model for predicting COP
        self.models['cop_prediction'] = RandomForestRegressor(**model_params)
        self.scalers['cop_prediction'] = StandardScaler()
        
        self.logger.info("Machine learning models initialized")
    
    async def update_data(self, current_status: Dict[str, Any], 
                         weather_data: List[Dict[str, Any]], 
                         prediction: Dict[str, Any],
                         timestamp: datetime):
        """Update learning data with new observations"""
        try:
            # Create data point
            data_point = {
                'timestamp': timestamp.isoformat(),
                'outside_temp': weather_data[0].get('temperature', 0) if weather_data else 0,
                'humidity': weather_data[0].get('humidity', 50) if weather_data else 50,
                'wind_speed': weather_data[0].get('wind_speed', 0) if weather_data else 0,
                'cloud_cover': weather_data[0].get('clouds', 0) if weather_data else 0,
                'room_temp': current_status.get('temperatures', {}).get('room', 20),
                'target_temp': current_status.get('temperatures', {}).get('target', 21),
                'outlet_temp': current_status.get('temperatures', {}).get('outlet', 0),
                'inlet_temp': current_status.get('temperatures', {}).get('inlet', 0),
                'pump_freq': current_status.get('system', {}).get('pump_frequency', 0),
                'compressor_freq': current_status.get('system', {}).get('compressor_frequency', 0),
                'energy_consumption': current_status.get('system', {}).get('energy_consumption', 0),
                'energy_production': current_status.get('system', {}).get('energy_production', 0),
                'cop': current_status.get('system', {}).get('cop', 0),
                'predicted_temp': prediction.get('target_temperature', 0),
                'predicted_cop': prediction.get('predicted_cop', 0),
                'hour_of_day': timestamp.hour,
                'day_of_week': timestamp.weekday(),
                'month': timestamp.month,
                'heating_system_type': self.config['house']['heating_system_type'],
                'building_mass': self._encode_building_mass(self.config['house']['building_thermal_mass'])
            }
            
            # Add to historical data
            self.historical_data.append(data_point)
            
            # Keep only recent data
            cutoff_date = timestamp - timedelta(days=self.max_data_age_days)
            self.historical_data = [
                dp for dp in self.historical_data 
                if datetime.fromisoformat(dp['timestamp']) > cutoff_date
            ]
            
            # Retrain models if we have enough data
            if len(self.historical_data) >= self.min_samples_for_learning:
                await self._retrain_models()
            
            # Save data periodically
            if len(self.historical_data) % 10 == 0:
                await self.save_data()
            
            self.logger.debug(f"Updated learning data. Total samples: {len(self.historical_data)}")
            
        except Exception as e:
            self.logger.error(f"Error updating learning data: {e}")
    
    def _encode_building_mass(self, mass_type: str) -> float:
        """Encode building mass type as numeric value"""
        mass_mapping = {
            'low': 1.0,
            'medium': 2.0,
            'high': 3.0
        }
        return mass_mapping.get(mass_type, 2.0)
    
    async def _retrain_models(self):
        """Retrain machine learning models with recent data"""
        try:
            if len(self.historical_data) < self.min_samples_for_learning:
                return
            
            df = pd.DataFrame(self.historical_data)
            
            # Prepare features for different models
            feature_columns = [
                'outside_temp', 'humidity', 'wind_speed', 'cloud_cover',
                'room_temp', 'target_temp', 'hour_of_day', 'day_of_week', 
                'month', 'building_mass'
            ]
            
            X = df[feature_columns].fillna(0)
            
            # Retrain temperature response model
            if 'outlet_temp' in df.columns and not df['outlet_temp'].isna().all():
                y_temp = df['outlet_temp'].fillna(method='forward')
                await self._train_model('temperature_response', X, y_temp)
            
            # Retrain energy consumption model  
            if 'energy_consumption' in df.columns and not df['energy_consumption'].isna().all():
                y_energy = df['energy_consumption'].fillna(method='forward')
                await self._train_model('energy_consumption', X, y_energy)
            
            # Retrain COP prediction model
            if 'cop' in df.columns and not df['cop'].isna().all():
                y_cop = df['cop'].fillna(method='forward')
                y_cop = y_cop[y_cop > 0]  # Remove invalid COP values
                if len(y_cop) > 10:
                    X_cop = X.loc[y_cop.index]
                    await self._train_model('cop_prediction', X_cop, y_cop)
            
            self.logger.info("Models retrained successfully")
            
        except Exception as e:
            self.logger.error(f"Error retraining models: {e}")
    
    async def _train_model(self, model_name: str, X: pd.DataFrame, y: pd.Series):
        """Train a specific model"""
        try:
            if len(X) < 10:  # Need minimum samples
                return
            
            # Scale features
            X_scaled = self.scalers[model_name].fit_transform(X)
            
            # Train model
            self.models[model_name].fit(X_scaled, y)
            
            # Calculate accuracy
            y_pred = self.models[model_name].predict(X_scaled)
            mae = mean_absolute_error(y, y_pred)
            
            # Store accuracy
            self.model_accuracy[model_name] = {
                'mae': mae,
                'samples': len(X),
                'trained_at': datetime.now().isoformat()
            }
            
            self.logger.debug(f"Trained {model_name} model. MAE: {mae:.3f}")
            
        except Exception as e:
            self.logger.error(f"Error training {model_name} model: {e}")
    
    def predict_temperature_response(self, conditions: Dict[str, Any]) -> Optional[float]:
        """Predict outlet temperature based on conditions"""
        return self._make_prediction('temperature_response', conditions)
    
    def predict_energy_consumption(self, conditions: Dict[str, Any]) -> Optional[float]:
        """Predict energy consumption based on conditions"""
        return self._make_prediction('energy_consumption', conditions)
    
    def predict_cop(self, conditions: Dict[str, Any]) -> Optional[float]:
        """Predict coefficient of performance"""
        return self._make_prediction('cop_prediction', conditions)
    
    def _make_prediction(self, model_name: str, conditions: Dict[str, Any]) -> Optional[float]:
        """Make prediction using specified model"""
        try:
            if model_name not in self.models:
                return None
            
            # Check if model is trained
            if not hasattr(self.models[model_name], 'n_features_in_'):
                return None
            
            # Prepare features
            features = np.array([[
                conditions.get('outside_temp', 0),
                conditions.get('humidity', 50),
                conditions.get('wind_speed', 0),
                conditions.get('cloud_cover', 0),
                conditions.get('room_temp', 20),
                conditions.get('target_temp', 21),
                conditions.get('hour_of_day', 12),
                conditions.get('day_of_week', 0),
                conditions.get('month', 1),
                conditions.get('building_mass', 2.0)
            ]])
            
            # Scale features
            features_scaled = self.scalers[model_name].transform(features)
            
            # Make prediction
            prediction = self.models[model_name].predict(features_scaled)[0]
            
            return float(prediction)
            
        except Exception as e:
            self.logger.error(f"Error making prediction with {model_name}: {e}")
            return None
    
    def calculate_thermal_lag(self, building_mass: str, heating_system: str) -> float:
        """Calculate thermal lag based on building characteristics"""
        
        # Base lag from configuration
        base_lag = self.config['advanced']['thermal_lag_hours']
        
        # Adjust for building mass
        mass_factors = {
            'low': 0.7,
            'medium': 1.0,
            'high': 1.5
        }
        mass_factor = mass_factors.get(building_mass, 1.0)
        
        # Adjust for heating system
        system_factors = {
            'radiator': 0.5,
            'underfloor': 1.2,
            'mixed': 0.8
        }
        system_factor = system_factors.get(heating_system, 1.0)
        
        # Learn from historical data if available
        if len(self.historical_data) > 50:
            learned_factor = self._calculate_learned_thermal_lag()
            total_lag = base_lag * mass_factor * system_factor * learned_factor
        else:
            total_lag = base_lag * mass_factor * system_factor
        
        return max(0.5, min(12.0, total_lag))  # Clamp between 0.5 and 12 hours
    
    def _calculate_learned_thermal_lag(self) -> float:
        """Calculate learned thermal lag factor from historical data"""
        try:
            # Analyze temperature response patterns
            df = pd.DataFrame(self.historical_data)
            
            if len(df) < 20:
                return 1.0
            
            # Calculate correlation between target temp changes and actual response
            df['temp_change'] = df['target_temp'].diff()
            df['room_temp_change'] = df['room_temp'].diff()
            
            # Simple correlation analysis
            correlation = df['temp_change'].corr(df['room_temp_change'])
            
            # Convert correlation to lag factor
            if correlation > 0.7:
                return 0.8  # Fast response
            elif correlation > 0.5:
                return 1.0  # Normal response
            else:
                return 1.3  # Slow response
                
        except Exception as e:
            self.logger.error(f"Error calculating learned thermal lag: {e}")
            return 1.0
    
    def get_learning_confidence(self) -> float:
        """Get overall confidence in learning algorithms"""
        if len(self.historical_data) < self.min_samples_for_learning:
            return 0.0
        
        confidence_factors = []
        
        # Data quantity factor
        data_factor = min(1.0, len(self.historical_data) / (self.min_samples_for_learning * 3))
        confidence_factors.append(data_factor)
        
        # Model accuracy factor
        for model_name, accuracy in self.model_accuracy.items():
            if 'mae' in accuracy:
                # Convert MAE to confidence (lower MAE = higher confidence)
                mae_confidence = max(0.0, 1.0 - (accuracy['mae'] / 10.0))
                confidence_factors.append(mae_confidence)
        
        if not confidence_factors:
            return 0.0
        
        return sum(confidence_factors) / len(confidence_factors)
    
    def get_adaptation_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for parameter adaptations"""
        recommendations = {
            'thermal_lag_adjustment': 1.0,
            'solar_gain_adjustment': 1.0,
            'wind_factor_adjustment': 1.0,
            'confidence': self.get_learning_confidence(),
            'data_points': len(self.historical_data)
        }
        
        if len(self.historical_data) < 50:
            return recommendations
        
        try:
            df = pd.DataFrame(self.historical_data)
            
            # Analyze thermal response
            if 'room_temp' in df.columns and 'target_temp' in df.columns:
                temp_responsiveness = self._analyze_temperature_responsiveness(df)
                recommendations['thermal_lag_adjustment'] = temp_responsiveness
            
            # Analyze weather impact
            weather_impact = self._analyze_weather_impact(df)
            recommendations.update(weather_impact)
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
        
        return recommendations
    
    def _analyze_temperature_responsiveness(self, df: pd.DataFrame) -> float:
        """Analyze how responsive the system is to temperature changes"""
        try:
            # Calculate response time to target temperature changes
            df['target_change'] = df['target_temp'].diff().abs()
            df['room_change'] = df['room_temp'].diff().abs()
            
            # Look at significant temperature changes (>0.5°C)
            significant_changes = df[df['target_change'] > 0.5]
            
            if len(significant_changes) < 5:
                return 1.0
            
            # Calculate average response ratio
            response_ratio = significant_changes['room_change'].mean() / significant_changes['target_change'].mean()
            
            # Convert to adjustment factor
            if response_ratio > 0.8:
                return 0.8  # Very responsive - reduce thermal lag
            elif response_ratio > 0.5:
                return 1.0  # Normal responsiveness
            else:
                return 1.3  # Slow responsiveness - increase thermal lag
                
        except Exception as e:
            self.logger.error(f"Error analyzing temperature responsiveness: {e}")
            return 1.0
    
    def _analyze_weather_impact(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analyze impact of weather on energy consumption"""
        impact = {
            'solar_gain_adjustment': 1.0,
            'wind_factor_adjustment': 1.0
        }
        
        try:
            if len(df) < 30:
                return impact
            
            # Analyze correlation between weather and energy consumption
            if 'energy_consumption' in df.columns:
                # Solar impact analysis
                if 'cloud_cover' in df.columns:
                    solar_corr = df['cloud_cover'].corr(df['energy_consumption'])
                    if abs(solar_corr) > 0.3:
                        # Strong correlation - adjust solar gain factor
                        impact['solar_gain_adjustment'] = 1.0 + (solar_corr * 0.5)
                
                # Wind impact analysis
                if 'wind_speed' in df.columns:
                    wind_corr = df['wind_speed'].corr(df['energy_consumption'])
                    if abs(wind_corr) > 0.3:
                        # Strong correlation - adjust wind factor
                        impact['wind_factor_adjustment'] = 1.0 + (wind_corr * 0.3)
            
        except Exception as e:
            self.logger.error(f"Error analyzing weather impact: {e}")
        
        return impact
    
    async def save_data(self):
        """Save learning data to file"""
        try:
            # Ensure data directory exists
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save data
            save_data = {
                'historical_data': self.historical_data,
                'model_accuracy': self.model_accuracy,
                'config_snapshot': {
                    'learning_rate': self.learning_rate,
                    'thermal_lag_hours': self.config['advanced']['thermal_lag_hours'],
                    'building_mass': self.config['house']['building_thermal_mass'],
                    'heating_system': self.config['house']['heating_system_type']
                },
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.data_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            self.logger.debug(f"Saved learning data to {self.data_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving learning data: {e}")
    
    def _load_data(self):
        """Load learning data from file"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                
                self.historical_data = data.get('historical_data', [])
                self.model_accuracy = data.get('model_accuracy', {})
                
                self.logger.info(f"Loaded {len(self.historical_data)} historical data points")
                
                # Retrain models if we have enough data
                if len(self.historical_data) >= self.min_samples_for_learning:
                    # Schedule retraining in background
                    import asyncio
                    asyncio.create_task(self._retrain_models())
            
        except Exception as e:
            self.logger.error(f"Error loading learning data: {e}")
            self.historical_data = []
            self.model_accuracy = {}