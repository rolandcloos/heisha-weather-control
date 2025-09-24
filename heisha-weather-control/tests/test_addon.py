#!/usr/bin/env python3
"""
Test suite for Heisha Weather Prediction Control
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from config_manager import ConfigManager
from weather_service import WeatherService
from learning_engine import LearningEngine
from predictive_algorithm import PredictiveAlgorithm
from heisha_controller import HeishaController
from mqtt_client import MQTTClient


class TestConfigManager:
    """Test configuration management"""
    
    def test_load_default_config(self):
        """Test loading default configuration"""
        with patch.dict(os.environ, {
            'MQTT_BROKER': 'test-broker',
            'WEATHER_API_KEY': 'test-key',
            'LATITUDE': '51.5',
            'LONGITUDE': '7.0'
        }):
            config_manager = ConfigManager()
            config = config_manager.load_config()
            
            assert config['mqtt']['broker'] == 'test-broker'
            assert config['weather']['api_key'] == 'test-key'
            assert config['house']['latitude'] == 51.5
            assert config['house']['longitude'] == 7.0
    
    def test_config_validation(self):
        """Test configuration validation"""
        config_manager = ConfigManager()
        
        # Test invalid latitude
        with pytest.raises(ValueError, match="Invalid latitude"):
            config_manager._validate_ranges({
                'house': {'latitude': 95.0, 'longitude': 0.0, 'target_temperature': 20.0},
                'advanced': {'solar_gain_factor': 0.5, 'wind_factor': 0.5}
            })
        
        # Test invalid temperature
        with pytest.raises(ValueError, match="Invalid target temperature"):
            config_manager._validate_ranges({
                'house': {'latitude': 50.0, 'longitude': 0.0, 'target_temperature': 35.0},
                'advanced': {'solar_gain_factor': 0.5, 'wind_factor': 0.5}
            })


class TestWeatherService:
    """Test weather service functionality"""
    
    @pytest.fixture
    def weather_service(self):
        """Create weather service instance"""
        return WeatherService(
            provider='openweathermap',
            api_key='test_key',
            latitude=51.5,
            longitude=7.0
        )
    
    def test_mock_data_generation(self, weather_service):
        """Test mock weather data generation"""
        weather_service._generate_mock_data()
        
        assert weather_service.current_weather
        assert 'temperature' in weather_service.current_weather
        assert len(weather_service.forecast_data) == 24
        
        # Check data structure
        forecast_item = weather_service.forecast_data[0]
        assert 'timestamp' in forecast_item
        assert 'temperature' in forecast_item
        assert 'humidity' in forecast_item
    
    def test_solar_radiation_calculation(self, weather_service):
        """Test solar radiation calculations"""
        # Test daytime
        daytime = datetime(2024, 6, 21, 12, 0)  # Summer solstice noon
        radiation = weather_service.calculate_solar_radiation(daytime, 0)  # No clouds
        assert radiation > 0
        
        # Test nighttime
        nighttime = datetime(2024, 6, 21, 23, 0)  # Night
        radiation = weather_service.calculate_solar_radiation(nighttime, 0)
        assert radiation == 0
        
        # Test cloudy conditions
        radiation_cloudy = weather_service.calculate_solar_radiation(daytime, 80)  # 80% clouds
        radiation_clear = weather_service.calculate_solar_radiation(daytime, 0)   # Clear
        assert radiation_cloudy < radiation_clear
    
    @pytest.mark.asyncio
    async def test_weather_summary(self, weather_service):
        """Test weather summary generation"""
        weather_service._generate_mock_data()
        summary = weather_service.get_weather_summary()
        
        required_fields = [
            'outside_temperature', 'humidity', 'wind_speed',
            'cloud_cover', 'solar_radiation', 'weather_description'
        ]
        
        for field in required_fields:
            assert field in summary


class TestLearningEngine:
    """Test learning engine functionality"""
    
    @pytest.fixture
    def config(self):
        """Sample configuration"""
        return {
            'advanced': {
                'learning_rate': 0.05,
                'thermal_lag_hours': 4.0
            },
            'house': {
                'building_thermal_mass': 'medium',
                'heating_system_type': 'underfloor'
            }
        }
    
    @pytest.fixture
    def learning_engine(self, config, tmp_path):
        """Create learning engine instance"""
        data_file = tmp_path / "test_learning.json"
        return LearningEngine(config, str(data_file))
    
    def test_initialization(self, learning_engine):
        """Test learning engine initialization"""
        assert learning_engine.models
        assert learning_engine.scalers
        assert 'temperature_response' in learning_engine.models
        assert 'energy_consumption' in learning_engine.models
        assert 'cop_prediction' in learning_engine.models
    
    def test_building_mass_encoding(self, learning_engine):
        """Test building mass encoding"""
        assert learning_engine._encode_building_mass('low') == 1.0
        assert learning_engine._encode_building_mass('medium') == 2.0
        assert learning_engine._encode_building_mass('high') == 3.0
        assert learning_engine._encode_building_mass('unknown') == 2.0  # Default
    
    def test_thermal_lag_calculation(self, learning_engine):
        """Test thermal lag calculations"""
        # Test different building masses
        lag_low = learning_engine.calculate_thermal_lag('low', 'radiator')
        lag_high = learning_engine.calculate_thermal_lag('high', 'underfloor')
        
        assert lag_low < lag_high
        assert 0.5 <= lag_low <= 12.0
        assert 0.5 <= lag_high <= 12.0
    
    @pytest.mark.asyncio
    async def test_data_update(self, learning_engine):
        """Test learning data updates"""
        current_status = {
            'temperatures': {'room': 21.0, 'target': 21.5, 'outlet': 35.0, 'inlet': 30.0},
            'system': {'pump_frequency': 50, 'compressor_frequency': 40, 'energy_consumption': 2.5, 'cop': 3.2}
        }
        
        weather_data = [{
            'temperature': 5.0, 'humidity': 60, 'wind_speed': 2.0, 'clouds': 30
        }]
        
        prediction = {
            'target_temperature': 21.5, 'predicted_cop': 3.0
        }
        
        await learning_engine.update_data(
            current_status, weather_data, prediction, datetime.now()
        )
        
        assert len(learning_engine.historical_data) == 1
        data_point = learning_engine.historical_data[0]
        assert data_point['room_temp'] == 21.0
        assert data_point['outside_temp'] == 5.0
    
    def test_confidence_calculation(self, learning_engine):
        """Test learning confidence calculation"""
        # Initially no confidence
        confidence = learning_engine.get_learning_confidence()
        assert confidence == 0.0
        
        # Add some mock data
        for i in range(150):  # Above minimum threshold
            learning_engine.historical_data.append({
                'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
                'outside_temp': 5.0 + i * 0.1,
                'room_temp': 21.0,
                'target_temp': 21.0
            })
        
        confidence = learning_engine.get_learning_confidence()
        assert confidence > 0.0


class TestPredictiveAlgorithm:
    """Test predictive algorithm functionality"""
    
    @pytest.fixture
    def config(self):
        """Sample configuration"""
        return {
            'advanced': {
                'prediction_horizon_hours': 24,
                'thermal_lag_hours': 4.0,
                'solar_gain_factor': 0.3,
                'wind_factor': 0.1
            },
            'house': {
                'target_temperature': 21.0,
                'night_setback': 2.0,
                'building_thermal_mass': 'medium',
                'heating_system_type': 'underfloor'
            }
        }
    
    @pytest.fixture
    def learning_engine_mock(self):
        """Mock learning engine"""
        mock = Mock()
        mock.get_learning_confidence.return_value = 0.5
        mock.calculate_thermal_lag.return_value = 4.0
        mock.predict_energy_consumption.return_value = None
        mock.predict_cop.return_value = None
        mock._encode_building_mass.return_value = 2.0
        return mock
    
    @pytest.fixture
    def predictive_algorithm(self, config, learning_engine_mock):
        """Create predictive algorithm instance"""
        return PredictiveAlgorithm(config, learning_engine_mock)
    
    def test_comfort_target_calculation(self, predictive_algorithm):
        """Test comfort target calculation"""
        # Test day time
        day_time = datetime(2024, 1, 1, 12, 0)
        target = predictive_algorithm._calculate_comfort_target(day_time)
        assert target == 21.0
        
        # Test night time
        night_time = datetime(2024, 1, 1, 23, 0)
        target = predictive_algorithm._calculate_comfort_target(night_time)
        assert target == 19.0  # 21.0 - 2.0 setback
    
    def test_solar_gain_calculation(self, predictive_algorithm):
        """Test solar gain calculations"""
        # Test noon (peak solar)
        noon = datetime(2024, 6, 21, 12, 0)
        gain = predictive_algorithm._calculate_solar_gain(noon, 0)  # No clouds
        assert gain > 0
        
        # Test night (no solar)
        night = datetime(2024, 6, 21, 23, 0)
        gain = predictive_algorithm._calculate_solar_gain(night, 0)
        assert gain == 0
        
        # Test cloudy vs clear
        gain_cloudy = predictive_algorithm._calculate_solar_gain(noon, 80)  # 80% clouds
        gain_clear = predictive_algorithm._calculate_solar_gain(noon, 0)   # Clear
        assert gain_cloudy < gain_clear
    
    def test_weather_impact_calculation(self, predictive_algorithm):
        """Test weather impact calculation"""
        weather_data = {
            'temperature': 5.0,
            'wind_speed': 5.0,
            'clouds': 50,
            'humidity': 60
        }
        
        forecast_time = datetime(2024, 6, 21, 12, 0)
        impact = predictive_algorithm._calculate_weather_impact(weather_data, forecast_time)
        
        assert 'solar_gain' in impact
        assert 'wind_loss' in impact
        assert 'humidity_factor' in impact
        assert 'total_impact' in impact
        
        # Wind should create loss (positive value)
        assert impact['wind_loss'] >= 0
        
        # Solar should create gain (positive value at noon)
        assert impact['solar_gain'] >= 0
    
    @pytest.mark.asyncio
    async def test_hourly_prediction(self, predictive_algorithm):
        """Test hourly condition predictions"""
        forecast_time = datetime.now() + timedelta(hours=1)
        weather_data = {
            'temperature': 5.0,
            'humidity': 60,
            'wind_speed': 3.0,
            'clouds': 40
        }
        
        current_status = {
            'temperatures': {'room': 20.0, 'outlet': 35.0}
        }
        
        prediction = await predictive_algorithm._predict_hourly_conditions(
            forecast_time, weather_data, current_status, 1
        )
        
        required_fields = [
            'hour_offset', 'outside_temp', 'comfort_target',
            'weather_impact', 'heat_demand', 'predicted_room_temp',
            'predicted_energy', 'predicted_cop'
        ]
        
        for field in required_fields:
            assert field in prediction
    
    def test_expected_cop_calculation(self, predictive_algorithm):
        """Test COP calculation"""
        # Test normal conditions
        cop = predictive_algorithm._calculate_expected_cop(5.0, 35.0)  # 30K difference
        assert 2.0 <= cop <= 6.0
        
        # Test better conditions (smaller temperature difference)
        cop_better = predictive_algorithm._calculate_expected_cop(15.0, 35.0)  # 20K difference
        assert cop_better > cop  # Should be more efficient
        
        # Test edge case
        cop_edge = predictive_algorithm._calculate_expected_cop(35.0, 35.0)  # No difference
        assert cop_edge == 6.0  # Max efficiency


class TestHeishaController:
    """Test Heisha controller functionality"""
    
    @pytest.fixture
    def mqtt_client_mock(self):
        """Mock MQTT client"""
        mock = Mock()
        mock.send_heisha_command = AsyncMock()
        mock.subscribe_to_topic = Mock()
        return mock
    
    @pytest.fixture
    def config(self):
        """Sample configuration"""
        return {
            'mqtt': {'topic_prefix': 'test_heat_pump'},
            'advanced': {'min_runtime_minutes': 30, 'max_modulation': 100}
        }
    
    @pytest.fixture
    def heisha_controller(self, mqtt_client_mock, config):
        """Create Heisha controller instance"""
        return HeishaController(mqtt_client_mock, config)
    
    def test_initialization(self, heisha_controller):
        """Test controller initialization"""
        assert heisha_controller.current_status == {}
        assert heisha_controller.last_update is None
        assert not heisha_controller.running
    
    def test_heishamon_data_processing(self, heisha_controller):
        """Test HeishaMon data processing"""
        # Test numeric data
        heisha_controller._on_heishamon_data(
            "test_heat_pump/main/Main_Outlet_Temp", "35.5"
        )
        
        assert 'Main_Outlet_Temp' in heisha_controller.current_status
        assert heisha_controller.current_status['Main_Outlet_Temp']['value'] == 35.5
        
        # Test integer data
        heisha_controller._on_heishamon_data(
            "test_heat_pump/main/Pump_Freq", "45"
        )
        
        assert heisha_controller.current_status['Pump_Freq']['value'] == 45
        
        # Test string data
        heisha_controller._on_heishamon_data(
            "test_heat_pump/main/Mode", "Heat"
        )
        
        assert heisha_controller.current_status['Mode']['value'] == "Heat"
    
    def test_parameter_retrieval(self, heisha_controller):
        """Test parameter retrieval"""
        # Add some test data
        heisha_controller.current_status = {
            'Main_Outlet_Temp': {'value': 35.5, 'timestamp': datetime.now()},
            'Pump_Freq': {'value': 45, 'timestamp': datetime.now()}
        }
        
        # Test existing parameter
        assert heisha_controller.get_parameter('Main_Outlet_Temp') == 35.5
        assert heisha_controller.get_parameter('Pump_Freq') == 45
        
        # Test non-existing parameter
        assert heisha_controller.get_parameter('Non_Existent') is None
    
    def test_heating_active_detection(self, heisha_controller):
        """Test heating activity detection"""
        # Test not heating
        assert not heisha_controller.is_heating_active()
        
        # Test heating (pump running)
        heisha_controller.current_status = {
            'Pump_Freq': {'value': 50, 'timestamp': datetime.now()}
        }
        assert heisha_controller.is_heating_active()
        
        # Test heating (compressor running)
        heisha_controller.current_status = {
            'Pump_Freq': {'value': 0, 'timestamp': datetime.now()},
            'Compressor_Freq': {'value': 30, 'timestamp': datetime.now()}
        }
        assert heisha_controller.is_heating_active()
    
    def test_cop_calculation(self, heisha_controller):
        """Test COP calculation"""
        # Test with valid data
        heisha_controller.current_status = {
            'Energy_Consumption': {'value': 2.0, 'timestamp': datetime.now()},
            'Energy_Production': {'value': 6.0, 'timestamp': datetime.now()}
        }
        
        cop = heisha_controller.get_current_cop()
        assert cop == 3.0  # 6.0 / 2.0
        
        # Test with no consumption
        heisha_controller.current_status['Energy_Consumption']['value'] = 0
        cop = heisha_controller.get_current_cop()
        assert cop is None
    
    @pytest.mark.asyncio
    async def test_temperature_setting(self, heisha_controller, mqtt_client_mock):
        """Test temperature setting"""
        # Test valid temperature
        await heisha_controller.set_target_temperature(22.5)
        mqtt_client_mock.send_heisha_command.assert_called_with(
            'SetZ1HeatRequestTemperature', 22
        )
        
        # Test invalid temperature (should be ignored)
        await heisha_controller.set_target_temperature(35.0)
        # Should not call MQTT command for invalid temperature
        assert mqtt_client_mock.send_heisha_command.call_count == 1
    
    @pytest.mark.asyncio 
    async def test_mode_setting(self, heisha_controller, mqtt_client_mock):
        """Test heat pump mode setting"""
        await heisha_controller.set_heat_pump_mode('heat')
        mqtt_client_mock.send_heisha_command.assert_called_with('SetHeatPump', 1)
        
        await heisha_controller.set_heat_pump_mode('off')
        mqtt_client_mock.send_heisha_command.assert_called_with('SetHeatPump', 0)


class TestMQTTClient:
    """Test MQTT client functionality"""
    
    @pytest.fixture
    def mqtt_client(self):
        """Create MQTT client instance"""
        return MQTTClient(
            broker='test-broker',
            port=1883,
            username='test-user',
            password='test-pass',
            topic_prefix='test_hp'
        )
    
    def test_initialization(self, mqtt_client):
        """Test MQTT client initialization"""
        assert mqtt_client.broker == 'test-broker'
        assert mqtt_client.port == 1883
        assert mqtt_client.topic_prefix == 'test_hp'
        assert not mqtt_client.connected
    
    @pytest.mark.asyncio
    async def test_publish_ha_sensor_data(self, mqtt_client):
        """Test Home Assistant sensor data publishing"""
        # Mock the publish method
        mqtt_client.publish = AsyncMock()
        
        await mqtt_client.update_ha_sensor('test_sensor', 25.5, '°C')
        
        # Verify publish was called
        mqtt_client.publish.assert_called_with(
            'test_hp/sensor/test_sensor/state', '25.5'
        )
    
    @pytest.mark.asyncio
    async def test_prediction_data_publishing(self, mqtt_client):
        """Test prediction data publishing"""
        mqtt_client.update_ha_sensor = AsyncMock()
        
        prediction_data = {
            'target_temperature': 21.5,
            'predicted_cop': 3.2,
            'learning_confidence': 0.75,
            'weather_impact': 1.2,
            'outside_temp_forecast': 5.0,
            'wind_speed': 3.0,
            'solar_radiation': 150
        }
        
        await mqtt_client.publish_prediction_data(prediction_data)
        
        # Verify multiple sensor updates were called
        assert mqtt_client.update_ha_sensor.call_count >= 4


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])