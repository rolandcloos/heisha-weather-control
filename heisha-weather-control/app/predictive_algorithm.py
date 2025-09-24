"""
Predictive Algorithm for Heisha Weather Prediction Control
Advanced predictive control algorithms with weather forecasting and learning
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from weather_service import WeatherService
from learning_engine import LearningEngine


class PredictiveAlgorithm:
    """Advanced predictive control algorithm for heat pump optimization"""
    
    def __init__(self, config: Dict[str, Any], learning_engine: LearningEngine):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.learning_engine = learning_engine
        
        # Control parameters
        self.prediction_horizon = config['advanced']['prediction_horizon_hours']
        self.thermal_lag = config['advanced']['thermal_lag_hours']
        self.solar_gain_factor = config['advanced']['solar_gain_factor']
        self.wind_factor = config['advanced']['wind_factor']
        
        # House parameters
        self.target_temperature = config['house']['target_temperature']
        self.night_setback = config['house']['night_setback']
        self.building_mass = config['house']['building_thermal_mass']
        self.heating_system = config['house']['heating_system_type']
        
        # Control state
        self.last_prediction = None
        self.control_history = []
        
        # Comfort zones
        self.comfort_zones = {
            'day': {'start': 6, 'end': 22, 'temp': self.target_temperature},
            'night': {'start': 22, 'end': 6, 'temp': self.target_temperature - self.night_setback}
        }
    
    async def predict(self, current_status: Dict[str, Any], 
                     weather_forecast: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Main prediction and control decision algorithm"""
        
        prediction_result = {
            'timestamp': datetime.now(),
            'action_needed': False,
            'settings': {},
            'predictions': [],
            'confidence': 0.0,
            'reasoning': []
        }
        
        try:
            # Get current conditions
            current_temp = current_status.get('temperatures', {}).get('room', 20.0)
            current_target = current_status.get('temperatures', {}).get('target', 21.0)
            outside_temp = current_status.get('temperatures', {}).get('outside', 10.0)
            
            # Calculate comfort target for each hour ahead
            hourly_predictions = []
            
            for hour in range(min(self.prediction_horizon, len(weather_forecast))):
                forecast_time = datetime.now() + timedelta(hours=hour)
                weather_data = weather_forecast[hour] if hour < len(weather_forecast) else weather_forecast[-1]
                
                # Predict conditions for this hour
                hour_prediction = await self._predict_hourly_conditions(
                    forecast_time, weather_data, current_status, hour
                )
                
                hourly_predictions.append(hour_prediction)
            
            prediction_result['predictions'] = hourly_predictions
            
            # Determine control actions
            control_decision = await self._calculate_control_actions(
                current_status, hourly_predictions
            )
            
            prediction_result.update(control_decision)
            
            # Update learning and adaptation
            await self._update_adaptive_parameters()
            
            # Store prediction for comparison
            self.last_prediction = prediction_result
            
            self.logger.debug(f"Prediction completed. Action needed: {prediction_result['action_needed']}")
            
        except Exception as e:
            self.logger.error(f"Error in prediction algorithm: {e}")
            prediction_result['error'] = str(e)
        
        return prediction_result
    
    async def _predict_hourly_conditions(self, forecast_time: datetime, 
                                       weather_data: Dict[str, Any],
                                       current_status: Dict[str, Any],
                                       hour_offset: int) -> Dict[str, Any]:
        """Predict conditions for a specific hour"""
        
        # Calculate comfort target for this time
        comfort_target = self._calculate_comfort_target(forecast_time)
        
        # Calculate weather influences
        weather_impact = self._calculate_weather_impact(weather_data, forecast_time)
        
        # Predict heat demand
        heat_demand = await self._predict_heat_demand(
            comfort_target, weather_data, current_status, hour_offset
        )
        
        # Predict system response
        system_response = await self._predict_system_response(
            heat_demand, weather_data, current_status
        )
        
        return {
            'hour_offset': hour_offset,
            'forecast_time': forecast_time.isoformat(),
            'outside_temp': weather_data.get('temperature', 0),
            'comfort_target': comfort_target,
            'weather_impact': weather_impact,
            'heat_demand': heat_demand,
            'predicted_room_temp': system_response.get('room_temp', comfort_target),
            'predicted_energy': system_response.get('energy_consumption', 0),
            'predicted_cop': system_response.get('cop', 3.0),
            'solar_gain': weather_impact.get('solar_gain', 0),
            'wind_loss': weather_impact.get('wind_loss', 0)
        }
    
    def _calculate_comfort_target(self, forecast_time: datetime) -> float:
        """Calculate target temperature based on time of day"""
        hour = forecast_time.hour
        
        # Determine if it's day or night
        if 6 <= hour < 22:  # Day time
            return self.target_temperature
        else:  # Night time
            return self.target_temperature - self.night_setback
    
    def _calculate_weather_impact(self, weather_data: Dict[str, Any], 
                                 forecast_time: datetime) -> Dict[str, Any]:
        """Calculate weather impact on building heat balance"""
        
        outside_temp = weather_data.get('temperature', 10)
        wind_speed = weather_data.get('wind_speed', 0)
        cloud_cover = weather_data.get('clouds', 0)
        humidity = weather_data.get('humidity', 50)
        
        # Solar gain calculation (simplified)
        solar_gain = self._calculate_solar_gain(forecast_time, cloud_cover)
        
        # Wind loss calculation
        wind_loss = wind_speed * self.wind_factor * max(0, 20 - outside_temp) / 20
        
        # Humidity impact on perceived temperature
        humidity_factor = 1.0 + (humidity - 50) / 500  # Small adjustment
        
        return {
            'solar_gain': solar_gain,
            'wind_loss': wind_loss,
            'humidity_factor': humidity_factor,
            'total_impact': solar_gain - wind_loss
        }
    
    def _calculate_solar_gain(self, forecast_time: datetime, cloud_cover: float) -> float:
        """Calculate solar heat gain"""
        hour = forecast_time.hour
        
        # Simple solar curve (peak at noon)
        if 6 <= hour <= 18:
            # Solar elevation approximation
            solar_elevation = np.sin(np.pi * (hour - 6) / 12)
            
            # Cloud reduction
            cloud_reduction = 1.0 - (cloud_cover / 100 * 0.8)
            
            # Maximum solar gain adjusted by factors
            max_solar_gain = 2.0  # °C equivalent
            solar_gain = max_solar_gain * solar_elevation * cloud_reduction * self.solar_gain_factor
            
            return max(0, solar_gain)
        
        return 0.0
    
    async def _predict_heat_demand(self, comfort_target: float, 
                                  weather_data: Dict[str, Any],
                                  current_status: Dict[str, Any],
                                  hour_offset: int) -> float:
        """Predict heat demand for maintaining comfort"""
        
        outside_temp = weather_data.get('temperature', 10)
        weather_impact = self._calculate_weather_impact(weather_data, datetime.now() + timedelta(hours=hour_offset))
        
        # Base heat demand (temperature difference)
        temp_difference = comfort_target - outside_temp
        base_demand = max(0, temp_difference * 0.5)  # Simplified heat loss coefficient
        
        # Adjust for weather impacts
        adjusted_demand = base_demand - weather_impact['total_impact']
        
        # Building thermal mass factor
        mass_factors = {'low': 1.2, 'medium': 1.0, 'high': 0.8}
        mass_factor = mass_factors.get(self.building_mass, 1.0)
        
        # Heating system efficiency factor
        system_factors = {'radiator': 1.1, 'underfloor': 0.9, 'mixed': 1.0}
        system_factor = system_factors.get(self.heating_system, 1.0)
        
        final_demand = adjusted_demand * mass_factor * system_factor
        
        # Use learning engine if available
        learned_demand = self.learning_engine.predict_energy_consumption({
            'outside_temp': outside_temp,
            'target_temp': comfort_target,
            'humidity': weather_data.get('humidity', 50),
            'wind_speed': weather_data.get('wind_speed', 0),
            'cloud_cover': weather_data.get('clouds', 0),
            'hour_of_day': (datetime.now() + timedelta(hours=hour_offset)).hour,
            'day_of_week': datetime.now().weekday(),
            'month': datetime.now().month,
            'building_mass': self.learning_engine._encode_building_mass(self.building_mass)
        })
        
        if learned_demand is not None:
            # Blend learned and calculated demand
            confidence = self.learning_engine.get_learning_confidence()
            final_demand = final_demand * (1 - confidence) + learned_demand * confidence
        
        return max(0, final_demand)
    
    async def _predict_system_response(self, heat_demand: float, 
                                      weather_data: Dict[str, Any],
                                      current_status: Dict[str, Any]) -> Dict[str, Any]:
        """Predict how the system will respond to heat demand"""
        
        # Current system state
        current_room_temp = current_status.get('temperatures', {}).get('room', 20)
        current_outlet_temp = current_status.get('temperatures', {}).get('outlet', 30)
        
        # Predict energy consumption
        predicted_energy = heat_demand * 1.2  # Simple conversion factor
        
        # Predict COP based on conditions
        outside_temp = weather_data.get('temperature', 10)
        predicted_cop = self._calculate_expected_cop(outside_temp, current_outlet_temp)
        
        # Use learning engine for better predictions
        learned_cop = self.learning_engine.predict_cop({
            'outside_temp': outside_temp,
            'target_temp': current_room_temp + 1,  # Assume 1°C increase target
            'humidity': weather_data.get('humidity', 50),
            'wind_speed': weather_data.get('wind_speed', 0),
            'cloud_cover': weather_data.get('clouds', 0),
            'room_temp': current_room_temp,
            'hour_of_day': datetime.now().hour,
            'day_of_week': datetime.now().weekday(),
            'month': datetime.now().month,
            'building_mass': self.learning_engine._encode_building_mass(self.building_mass)
        })
        
        if learned_cop is not None:
            confidence = self.learning_engine.get_learning_confidence()
            predicted_cop = predicted_cop * (1 - confidence) + learned_cop * confidence
        
        # Predict room temperature response
        thermal_lag = self.learning_engine.calculate_thermal_lag(self.building_mass, self.heating_system)
        temp_response = heat_demand * 0.5 * (1 - np.exp(-1 / thermal_lag))
        predicted_room_temp = current_room_temp + temp_response
        
        return {
            'room_temp': predicted_room_temp,
            'energy_consumption': predicted_energy,
            'cop': max(1.0, min(6.0, predicted_cop)),
            'thermal_lag_used': thermal_lag
        }
    
    def _calculate_expected_cop(self, outside_temp: float, outlet_temp: float) -> float:
        """Calculate expected COP based on temperatures"""
        # Simplified COP calculation based on temperature difference
        temp_diff = outlet_temp - outside_temp
        
        if temp_diff <= 0:
            return 6.0  # Very efficient (unrealistic scenario)
        
        # Carnot efficiency approximation with practical factors
        carnot_cop = (outlet_temp + 273.15) / temp_diff
        practical_cop = carnot_cop * 0.45  # Practical efficiency factor
        
        return max(2.0, min(6.0, practical_cop))
    
    async def _calculate_control_actions(self, current_status: Dict[str, Any], 
                                       predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate required control actions based on predictions"""
        
        control_result = {
            'action_needed': False,
            'settings': {},
            'confidence': self.learning_engine.get_learning_confidence(),
            'reasoning': []
        }
        
        if not predictions:
            return control_result
        
        current_temp = current_status.get('temperatures', {}).get('room', 20)
        current_target = current_status.get('temperatures', {}).get('target', 21)
        
        # Analyze next few hours for proactive control
        immediate_predictions = predictions[:6]  # Next 6 hours
        
        # Check if we need to start heating early due to thermal lag
        thermal_lag = self.learning_engine.calculate_thermal_lag(self.building_mass, self.heating_system)
        
        # Find upcoming temperature needs
        upcoming_targets = [p['comfort_target'] for p in immediate_predictions]
        max_upcoming_target = max(upcoming_targets) if upcoming_targets else current_target
        
        # Calculate lead time needed
        temp_increase_needed = max_upcoming_target - current_temp
        
        if temp_increase_needed > 1.0:  # Significant temperature increase needed
            # Calculate when to start heating
            hours_ahead_to_start = min(thermal_lag, len(predictions))
            
            # Check if we should start heating now for future demand
            future_prediction = predictions[int(hours_ahead_to_start)] if hours_ahead_to_start < len(predictions) else predictions[-1]
            
            if future_prediction['comfort_target'] > current_temp + 0.5:
                control_result['action_needed'] = True
                control_result['settings']['target_temperature'] = max_upcoming_target
                control_result['reasoning'].append(f"Proactive heating for {hours_ahead_to_start:.1f}h thermal lag")
        
        # Check for immediate comfort issues
        immediate_target = predictions[0]['comfort_target']
        temp_error = immediate_target - current_temp
        
        if abs(temp_error) > 0.5:  # More than 0.5°C error
            control_result['action_needed'] = True
            
            # Calculate optimal target temperature considering predictions
            optimal_target = self._calculate_optimal_target(predictions, current_status)
            control_result['settings']['target_temperature'] = optimal_target
            control_result['reasoning'].append(f"Temperature error: {temp_error:.1f}°C")
        
        # Energy optimization check
        energy_optimization = self._calculate_energy_optimization(predictions)
        if energy_optimization['action_needed']:
            control_result['action_needed'] = True
            control_result['settings'].update(energy_optimization['settings'])
            control_result['reasoning'].extend(energy_optimization['reasoning'])
        
        # Weather-based adjustments
        weather_adjustments = self._calculate_weather_adjustments(predictions)
        if weather_adjustments['action_needed']:
            control_result['action_needed'] = True
            control_result['settings'].update(weather_adjustments['settings'])
            control_result['reasoning'].extend(weather_adjustments['reasoning'])
        
        return control_result
    
    def _calculate_optimal_target(self, predictions: List[Dict[str, Any]], 
                                 current_status: Dict[str, Any]) -> float:
        """Calculate optimal target temperature considering future needs"""
        
        if not predictions:
            return self.target_temperature
        
        # Weight near-term predictions more heavily
        weighted_targets = []
        weights = []
        
        for i, pred in enumerate(predictions[:12]):  # Next 12 hours
            weight = 1.0 / (i + 1)  # Decreasing weight with time
            weighted_targets.append(pred['comfort_target'] * weight)
            weights.append(weight)
        
        if not weighted_targets:
            return self.target_temperature
        
        optimal_target = sum(weighted_targets) / sum(weights)
        
        # Adjust for thermal lag - if we need higher temperature later, increase now
        thermal_lag = self.learning_engine.calculate_thermal_lag(self.building_mass, self.heating_system)
        lag_hours = int(thermal_lag)
        
        if lag_hours < len(predictions):
            future_target = predictions[lag_hours]['comfort_target']
            current_target = predictions[0]['comfort_target']
            lag_adjustment = (future_target - current_target) * 0.5
            optimal_target += lag_adjustment
        
        # Clamp to reasonable bounds
        return max(15.0, min(30.0, optimal_target))
    
    def _calculate_energy_optimization(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate energy optimization opportunities"""
        
        result = {
            'action_needed': False,
            'settings': {},
            'reasoning': []
        }
        
        if len(predictions) < 6:
            return result
        
        # Look for periods of high solar gain
        solar_periods = [p for p in predictions[:12] if p.get('solar_gain', 0) > 1.0]
        
        if solar_periods:
            # During high solar gain, we can reduce heating slightly
            avg_solar_gain = np.mean([p['solar_gain'] for p in solar_periods])
            if avg_solar_gain > 1.5:
                # Reduce target temperature slightly during solar gain periods
                solar_reduction = min(1.0, avg_solar_gain * 0.3)
                current_target = predictions[0]['comfort_target']
                
                result['action_needed'] = True
                result['settings']['target_temperature'] = current_target - solar_reduction
                result['reasoning'].append(f"Solar gain optimization: -{solar_reduction:.1f}°C")
        
        # Look for periods of low energy cost (if we had pricing data)
        # This would be where we pre-heat during cheap periods
        
        return result
    
    def _calculate_weather_adjustments(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate weather-based control adjustments"""
        
        result = {
            'action_needed': False,
            'settings': {},
            'reasoning': []
        }
        
        if len(predictions) < 3:
            return result
        
        # Check for incoming cold weather
        current_outside = predictions[0].get('outside_temp', 10)
        future_outside_temps = [p.get('outside_temp', 10) for p in predictions[1:6]]
        
        if future_outside_temps:
            min_future_temp = min(future_outside_temps)
            temp_drop = current_outside - min_future_temp
            
            if temp_drop > 5.0:  # Significant temperature drop expected
                # Pre-heat to compensate for thermal lag
                preheat_adjustment = min(2.0, temp_drop * 0.2)
                
                result['action_needed'] = True
                current_target = predictions[0]['comfort_target']
                result['settings']['target_temperature'] = current_target + preheat_adjustment
                result['reasoning'].append(f"Cold weather preparation: +{preheat_adjustment:.1f}°C")
        
        # Check for strong wind periods
        wind_speeds = [p.get('weather_impact', {}).get('wind_loss', 0) for p in predictions[:6]]
        if wind_speeds and max(wind_speeds) > 1.0:
            max_wind_loss = max(wind_speeds)
            wind_adjustment = min(1.5, max_wind_loss * 0.5)
            
            if not result['action_needed']:
                result['action_needed'] = True
                current_target = predictions[0]['comfort_target']
                result['settings']['target_temperature'] = current_target + wind_adjustment
                result['reasoning'].append(f"Wind compensation: +{wind_adjustment:.1f}°C")
            else:
                # Add to existing adjustment
                result['settings']['target_temperature'] += wind_adjustment
                result['reasoning'].append(f"Wind compensation: +{wind_adjustment:.1f}°C")
        
        return result
    
    async def _update_adaptive_parameters(self):
        """Update algorithm parameters based on learning"""
        
        # Get learning recommendations
        recommendations = self.learning_engine.get_adaptation_recommendations()
        
        confidence = recommendations.get('confidence', 0)
        
        if confidence > 0.7:  # High confidence in learning
            # Adapt thermal lag
            thermal_adjustment = recommendations.get('thermal_lag_adjustment', 1.0)
            self.thermal_lag = self.config['advanced']['thermal_lag_hours'] * thermal_adjustment
            
            # Adapt solar gain factor
            solar_adjustment = recommendations.get('solar_gain_adjustment', 1.0) 
            self.solar_gain_factor = self.config['advanced']['solar_gain_factor'] * solar_adjustment
            
            # Adapt wind factor
            wind_adjustment = recommendations.get('wind_factor_adjustment', 1.0)
            self.wind_factor = self.config['advanced']['wind_factor'] * wind_adjustment
            
            self.logger.debug(f"Adapted parameters - Thermal lag: {self.thermal_lag:.1f}h, "
                            f"Solar gain: {self.solar_gain_factor:.2f}, "
                            f"Wind factor: {self.wind_factor:.2f}")
    
    def get_algorithm_status(self) -> Dict[str, Any]:
        """Get current algorithm status and parameters"""
        
        return {
            'current_parameters': {
                'thermal_lag_hours': self.thermal_lag,
                'solar_gain_factor': self.solar_gain_factor,
                'wind_factor': self.wind_factor,
                'prediction_horizon_hours': self.prediction_horizon
            },
            'learning_confidence': self.learning_engine.get_learning_confidence(),
            'historical_data_points': len(self.learning_engine.historical_data),
            'last_prediction_time': self.last_prediction['timestamp'].isoformat() if self.last_prediction else None,
            'comfort_zones': self.comfort_zones
        }