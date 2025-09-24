"""
MQTT Client for Heisha Weather Prediction Control
Handles communication with Home Assistant and HeishaMon
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable

import paho.mqtt.client as mqtt


class MQTTClient:
    """MQTT client for communication with HeishaMon and Home Assistant"""
    
    def __init__(self, broker: str, port: int, username: str = None, 
                 password: str = None, topic_prefix: str = "panasonic_heat_pump"):
        self.logger = logging.getLogger(__name__)
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.topic_prefix = topic_prefix
        
        self.client = None
        self.connected = False
        self.message_callbacks = {}
        
        # Home Assistant discovery topics
        self.ha_discovery_prefix = "homeassistant"
        
    async def connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            self.client = mqtt.Client(client_id="heisha_weather_control")
            
            # Set credentials if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Connect to broker
            self.logger.info(f"Connecting to MQTT broker {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port, 60)
            
            # Start loop in background
            self.client.loop_start()
            
            # Wait for connection
            for _ in range(30):  # Wait up to 30 seconds
                if self.connected:
                    break
                await asyncio.sleep(1)
            
            if not self.connected:
                raise ConnectionError("Failed to connect to MQTT broker within timeout")
            
            # Subscribe to HeishaMon topics
            await self._subscribe_to_heishamon()
            
            # Publish Home Assistant discovery messages
            await self._publish_ha_discovery()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            self.connected = True
            self.logger.info("Connected to MQTT broker successfully")
        else:
            self.logger.error(f"Failed to connect to MQTT broker, return code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.connected = False
        if rc != 0:
            self.logger.warning("Unexpected MQTT disconnection")
        else:
            self.logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Callback for MQTT messages"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Handle JSON payloads
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = payload
            
            # Call registered callbacks
            for pattern, callback in self.message_callbacks.items():
                if pattern in topic:
                    callback(topic, data)
                    
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")
    
    async def _subscribe_to_heishamon(self):
        """Subscribe to HeishaMon topics"""
        topics = [
            f"{self.topic_prefix}/main/+",
            f"{self.topic_prefix}/1wire/+",
            f"{self.topic_prefix}/stats",
        ]
        
        for topic in topics:
            self.client.subscribe(topic)
            self.logger.debug(f"Subscribed to topic: {topic}")
    
    async def _publish_ha_discovery(self):
        """Publish Home Assistant discovery messages"""
        device_info = {
            "identifiers": ["heisha_weather_control"],
            "name": "Heisha Weather Control",
            "model": "Weather Predictive Controller",
            "manufacturer": "Heisha Weather Control",
            "sw_version": "1.0.0"
        }
        
        # Climate entity
        climate_config = {
            "name": "Heisha Heat Pump",
            "unique_id": "heisha_climate",
            "device": device_info,
            "temperature_command_topic": f"{self.topic_prefix}/commands/SetZ1HeatRequestTemperature",
            "temperature_state_topic": f"{self.topic_prefix}/main/Z1_Heat_Request_Temp",
            "current_temperature_topic": f"{self.topic_prefix}/main/Room_Thermostat_Temp",
            "mode_command_topic": f"{self.topic_prefix}/commands/SetHeatPump",
            "mode_state_topic": f"{self.topic_prefix}/main/Heatpump_State",
            "modes": ["off", "heat"],
            "min_temp": 15,
            "max_temp": 30,
            "temp_step": 0.5,
            "temperature_unit": "C"
        }
        
        await self.publish(
            f"{self.ha_discovery_prefix}/climate/heisha/config",
            json.dumps(climate_config),
            retain=True
        )
        
        # Temperature sensors
        sensors = [
            {
                "name": "Heisha Outlet Temperature",
                "unique_id": "heisha_outlet_temp",
                "state_topic": f"{self.topic_prefix}/main/Main_Outlet_Temp",
                "unit_of_measurement": "°C",
                "device_class": "temperature"
            },
            {
                "name": "Heisha Inlet Temperature", 
                "unique_id": "heisha_inlet_temp",
                "state_topic": f"{self.topic_prefix}/main/Main_Inlet_Temp",
                "unit_of_measurement": "°C",
                "device_class": "temperature"
            },
            {
                "name": "Heisha Outside Temperature",
                "unique_id": "heisha_outside_temp", 
                "state_topic": f"{self.topic_prefix}/main/Outside_Temp",
                "unit_of_measurement": "°C",
                "device_class": "temperature"
            },
            {
                "name": "Heisha Energy Consumption",
                "unique_id": "heisha_energy",
                "state_topic": f"{self.topic_prefix}/main/Energy_Consumption",
                "unit_of_measurement": "kW",
                "device_class": "power"
            }
        ]
        
        for sensor in sensors:
            sensor["device"] = device_info
            await self.publish(
                f"{self.ha_discovery_prefix}/sensor/heisha/{sensor['unique_id']}/config",
                json.dumps(sensor),
                retain=True
            )
        
        self.logger.info("Published Home Assistant discovery messages")
    
    async def publish(self, topic: str, payload: str, retain: bool = False):
        """Publish message to MQTT topic"""
        if not self.connected:
            self.logger.warning("Cannot publish - MQTT not connected")
            return
        
        try:
            self.client.publish(topic, payload, retain=retain)
            self.logger.debug(f"Published to {topic}: {payload}")
        except Exception as e:
            self.logger.error(f"Failed to publish to {topic}: {e}")
    
    def subscribe_to_topic(self, topic: str, callback: Callable):
        """Subscribe to a topic with callback"""
        self.message_callbacks[topic] = callback
        if self.connected:
            self.client.subscribe(topic)
    
    async def send_heisha_command(self, command: str, value: Any):
        """Send command to HeishaMon"""
        topic = f"{self.topic_prefix}/commands/{command}"
        await self.publish(topic, str(value))
        self.logger.info(f"Sent HeishaMon command: {command} = {value}")
    
    async def update_ha_sensor(self, sensor_name: str, value: Any, unit: str = None):
        """Update Home Assistant sensor value"""
        topic = f"{self.topic_prefix}/sensor/{sensor_name}/state"
        
        if isinstance(value, dict):
            payload = json.dumps(value)
        else:
            payload = str(value)
        
        await self.publish(topic, payload)
        
        # Also publish attributes if it's a dict
        if isinstance(value, dict) and 'value' in value:
            await self.publish(f"{topic}/attributes", json.dumps({
                k: v for k, v in value.items() if k != 'value'
            }))
    
    async def publish_prediction_data(self, prediction_data: Dict[str, Any]):
        """Publish prediction data to Home Assistant"""
        
        # Current prediction
        await self.update_ha_sensor("prediction_target_temp", 
                                  prediction_data.get('target_temperature', 0))
        
        # Efficiency metrics
        await self.update_ha_sensor("prediction_efficiency", 
                                  prediction_data.get('predicted_cop', 0))
        
        # Learning progress
        await self.update_ha_sensor("learning_progress", 
                                  prediction_data.get('learning_confidence', 0))
        
        # Weather influence
        weather_influence = {
            'value': prediction_data.get('weather_impact', 0),
            'outside_temp': prediction_data.get('outside_temp_forecast', 0),
            'wind_speed': prediction_data.get('wind_speed', 0),
            'solar_radiation': prediction_data.get('solar_radiation', 0)
        }
        
        await self.update_ha_sensor("weather_influence", weather_influence)
        
        self.logger.debug("Published prediction data to Home Assistant")