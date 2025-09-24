#!/usr/bin/env python3
"""
Heisha Weather Prediction Control
Main application entry point for Home Assistant Add-On
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

from heisha_controller import HeishaController
from weather_service import WeatherService
from predictive_algorithm import PredictiveAlgorithm
from learning_engine import LearningEngine
from mqtt_client import MQTTClient
from config_manager import ConfigManager

# Setup logging
def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration"""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

class HeishaWeatherControl:
    """Main application class for Heisha Weather Prediction Control"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # Initialize components
        self.mqtt_client = None
        self.weather_service = None
        self.heisha_controller = None
        self.predictive_algorithm = None
        self.learning_engine = None
        
        self.running = False
        
    async def initialize(self) -> bool:
        """Initialize all components"""
        try:
            self.logger.info("Initializing Heisha Weather Prediction Control...")
            
            # Initialize MQTT client
            self.mqtt_client = MQTTClient(
                broker=self.config['mqtt']['broker'],
                port=self.config['mqtt']['port'],
                username=self.config['mqtt'].get('username'),
                password=self.config['mqtt'].get('password'),
                topic_prefix=self.config['mqtt']['topic_prefix']
            )
            
            # Initialize weather service
            self.weather_service = WeatherService(
                provider=self.config['weather']['api_provider'],
                api_key=self.config['weather']['api_key'],
                latitude=self.config['house']['latitude'],
                longitude=self.config['house']['longitude'],
                update_interval=self.config['weather']['update_interval']
            )
            
            # Initialize Heisha controller
            self.heisha_controller = HeishaController(
                mqtt_client=self.mqtt_client,
                config=self.config
            )
            
            # Initialize learning engine
            self.learning_engine = LearningEngine(
                config=self.config,
                data_path="/data/learning_data.json"
            )
            
            # Initialize predictive algorithm
            self.predictive_algorithm = PredictiveAlgorithm(
                config=self.config,
                learning_engine=self.learning_engine
            )
            
            # Connect MQTT
            await self.mqtt_client.connect()
            self.logger.info("MQTT connected successfully")
            
            # Initialize weather service
            await self.weather_service.initialize()
            self.logger.info("Weather service initialized")
            
            # Initialize Heisha controller
            await self.heisha_controller.initialize()
            self.logger.info("Heisha controller initialized")
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            return False
    
    async def run_control_loop(self):
        """Main control loop"""
        self.logger.info("Starting predictive control loop")
        
        while self.running:
            try:
                # Get current status from heat pump
                current_status = await self.heisha_controller.get_status()
                
                # Get weather forecast
                weather_forecast = await self.weather_service.get_forecast()
                
                # Run predictive algorithm
                prediction = await self.predictive_algorithm.predict(
                    current_status=current_status,
                    weather_forecast=weather_forecast
                )
                
                # Apply control decisions
                if prediction['action_needed']:
                    await self.heisha_controller.apply_settings(prediction['settings'])
                    self.logger.info(f"Applied new settings: {prediction['settings']}")
                
                # Update learning engine with results
                await self.learning_engine.update_data(
                    current_status=current_status,
                    weather_data=weather_forecast,
                    prediction=prediction,
                    timestamp=datetime.now()
                )
                
                # Sleep for next iteration (default: 5 minutes)
                await asyncio.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Error in control loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def start(self):
        """Start the application"""
        self.running = True
        
        if not await self.initialize():
            self.logger.error("Failed to initialize application")
            return
        
        self.logger.info("Heisha Weather Prediction Control started successfully")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self.run_control_loop()),
            asyncio.create_task(self.weather_service.start_updates()),
            asyncio.create_task(self.heisha_controller.monitor_status())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the application"""
        self.logger.info("Shutting down Heisha Weather Prediction Control...")
        self.running = False
        
        if self.mqtt_client:
            await self.mqtt_client.disconnect()
        
        if self.weather_service:
            await self.weather_service.stop()
        
        if self.learning_engine:
            await self.learning_engine.save_data()
        
        self.logger.info("Shutdown complete")

def main():
    """Main entry point"""
    # Setup logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Heisha Weather Prediction Control Add-On")
    
    # Create and run application
    app = HeishaWeatherControl()
    
    try:
        asyncio.run(app.start())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()