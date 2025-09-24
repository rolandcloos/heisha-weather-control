"""
Configuration Manager for Heisha Weather Prediction Control
Handles loading and validation of configuration from Home Assistant
"""

import json
import os
import logging
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages configuration loading and validation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_file = os.getenv('CONFIG_FILE', '/data/options.json')
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from Home Assistant options"""
        try:
            # First try to load from file
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                # Fallback to environment variables
                config = self._load_from_env()
                self.logger.info("Configuration loaded from environment variables")
            
            # Validate and set defaults
            config = self._validate_and_set_defaults(config)
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables as fallback"""
        return {
            'mqtt': {
                'broker': os.getenv('MQTT_BROKER', 'core-mosquitto'),
                'port': int(os.getenv('MQTT_PORT', '1883')),
                'username': os.getenv('MQTT_USERNAME', ''),
                'password': os.getenv('MQTT_PASSWORD', ''),
                'topic_prefix': os.getenv('TOPIC_PREFIX', 'panasonic_heat_pump')
            },
            'weather': {
                'api_provider': os.getenv('WEATHER_PROVIDER', 'openweathermap'),
                'api_key': os.getenv('WEATHER_API_KEY', ''),
                'update_interval': int(os.getenv('WEATHER_UPDATE_INTERVAL', '300'))
            },
            'house': {
                'latitude': float(os.getenv('LATITUDE', '51.1657')),
                'longitude': float(os.getenv('LONGITUDE', '10.4515')),
                'timezone': os.getenv('TIMEZONE', 'Europe/Berlin'),
                'heating_system_type': os.getenv('HEATING_SYSTEM_TYPE', 'underfloor'),
                'building_thermal_mass': os.getenv('BUILDING_THERMAL_MASS', 'medium'),
                'target_temperature': float(os.getenv('TARGET_TEMPERATURE', '21.0')),
                'night_setback': float(os.getenv('NIGHT_SETBACK', '2.0'))
            },
            'advanced': {
                'thermal_lag_hours': 4.0,
                'solar_gain_factor': 0.3,
                'wind_factor': 0.1,
                'learning_rate': 0.05,
                'prediction_horizon_hours': 24,
                'min_runtime_minutes': 30,
                'max_modulation': 100
            },
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO')
            }
        }
    
    def _validate_and_set_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration and set defaults"""
        
        # MQTT validation
        if 'mqtt' not in config:
            config['mqtt'] = {}
        
        mqtt_defaults = {
            'broker': 'core-mosquitto',
            'port': 1883,
            'username': '',
            'password': '',
            'topic_prefix': 'panasonic_heat_pump'
        }
        
        for key, default in mqtt_defaults.items():
            if key not in config['mqtt']:
                config['mqtt'][key] = default
        
        # Weather validation
        if 'weather' not in config:
            config['weather'] = {}
        
        weather_defaults = {
            'api_provider': 'openweathermap',
            'api_key': '',
            'update_interval': 300
        }
        
        for key, default in weather_defaults.items():
            if key not in config['weather']:
                config['weather'][key] = default
        
        if not config['weather']['api_key']:
            self.logger.warning("No weather API key provided - weather features will be limited")
        
        # House configuration validation
        if 'house' not in config:
            config['house'] = {}
        
        house_defaults = {
            'latitude': 51.1657,
            'longitude': 10.4515,
            'timezone': 'Europe/Berlin',
            'heating_system_type': 'underfloor',
            'building_thermal_mass': 'medium',
            'target_temperature': 21.0,
            'night_setback': 2.0
        }
        
        for key, default in house_defaults.items():
            if key not in config['house']:
                config['house'][key] = default
        
        # Advanced configuration validation
        if 'advanced' not in config:
            config['advanced'] = {}
        
        advanced_defaults = {
            'thermal_lag_hours': 4.0,
            'solar_gain_factor': 0.3,
            'wind_factor': 0.1,
            'learning_rate': 0.05,
            'prediction_horizon_hours': 24,
            'min_runtime_minutes': 30,
            'max_modulation': 100
        }
        
        for key, default in advanced_defaults.items():
            if key not in config['advanced']:
                config['advanced'][key] = default
        
        # Logging validation
        if 'logging' not in config:
            config['logging'] = {}
        
        if 'level' not in config['logging']:
            config['logging']['level'] = 'INFO'
        
        # Validate ranges
        self._validate_ranges(config)
        
        return config
    
    def _validate_ranges(self, config: Dict[str, Any]):
        """Validate configuration value ranges"""
        
        # Coordinate validation
        lat = config['house']['latitude']
        lon = config['house']['longitude']
        
        if not (-90 <= lat <= 90):
            raise ValueError(f"Invalid latitude: {lat}. Must be between -90 and 90")
        
        if not (-180 <= lon <= 180):
            raise ValueError(f"Invalid longitude: {lon}. Must be between -180 and 180")
        
        # Temperature validation
        target_temp = config['house']['target_temperature']
        if not (15 <= target_temp <= 30):
            raise ValueError(f"Invalid target temperature: {target_temp}. Must be between 15 and 30°C")
        
        # Advanced parameter validation
        adv = config['advanced']
        
        if not (0.5 <= adv['thermal_lag_hours'] <= 12):
            self.logger.warning(f"thermal_lag_hours {adv['thermal_lag_hours']} outside recommended range 0.5-12")
        
        if not (0 <= adv['solar_gain_factor'] <= 1):
            raise ValueError(f"solar_gain_factor must be between 0 and 1, got {adv['solar_gain_factor']}")
        
        if not (0 <= adv['wind_factor'] <= 1):
            raise ValueError(f"wind_factor must be between 0 and 1, got {adv['wind_factor']}")
        
        if not (0.001 <= adv['learning_rate'] <= 0.5):
            self.logger.warning(f"learning_rate {adv['learning_rate']} outside recommended range 0.001-0.5")
        
        self.logger.info("Configuration validation completed successfully")