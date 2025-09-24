"""
Heisha Controller for Panasonic Heat Pump via HeishaMon/MQTT
Handles communication with the heat pump and status monitoring
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from mqtt_client import MQTTClient


class HeishaController:
    """Controller for Panasonic heat pump via HeishaMon"""
    
    def __init__(self, mqtt_client: MQTTClient, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.mqtt_client = mqtt_client
        self.config = config
        
        # Heat pump status
        self.current_status = {}
        self.last_update = None
        
        # Control parameters
        self.min_runtime = timedelta(minutes=config['advanced']['min_runtime_minutes'])
        self.max_modulation = config['advanced']['max_modulation']
        
        # Operating modes
        self.heat_pump_modes = {
            0: 'off',
            1: 'heat',
            2: 'cool', 
            3: 'auto'
        }
        
        self.running = False
        
    async def initialize(self) -> bool:
        """Initialize the controller"""
        try:
            # Subscribe to HeishaMon status topics
            self.mqtt_client.subscribe_to_topic(
                f"{self.config['mqtt']['topic_prefix']}/main/",
                self._on_heishamon_data
            )
            
            # Subscribe to 1-wire sensor topics  
            self.mqtt_client.subscribe_to_topic(
                f"{self.config['mqtt']['topic_prefix']}/1wire/",
                self._on_sensor_data
            )
            
            self.logger.info("Heisha controller initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Heisha controller: {e}")
            return False
    
    def _on_heishamon_data(self, topic: str, data: Any):
        """Handle incoming HeishaMon data"""
        try:
            # Extract parameter name from topic
            topic_parts = topic.split('/')
            if len(topic_parts) >= 3:
                param_name = topic_parts[-1]
                
                # Convert numeric strings to numbers
                if isinstance(data, str) and data.replace('.', '').replace('-', '').isdigit():
                    data = float(data) if '.' in data else int(data)
                
                self.current_status[param_name] = {
                    'value': data,
                    'timestamp': datetime.now()
                }
                
                self.last_update = datetime.now()
                
                # Log important status changes
                if param_name in ['Heatpump_State', 'Main_Outlet_Temp', 'Room_Thermostat_Temp']:
                    self.logger.debug(f"HeishaMon update: {param_name} = {data}")
                    
        except Exception as e:
            self.logger.error(f"Error processing HeishaMon data: {e}")
    
    def _on_sensor_data(self, topic: str, data: Any):
        """Handle 1-wire sensor data"""
        try:
            topic_parts = topic.split('/')
            if len(topic_parts) >= 3:
                sensor_name = topic_parts[-1]
                
                if isinstance(data, str) and data.replace('.', '').replace('-', '').isdigit():
                    data = float(data)
                
                self.current_status[f"sensor_{sensor_name}"] = {
                    'value': data,
                    'timestamp': datetime.now()
                }
                
        except Exception as e:
            self.logger.error(f"Error processing sensor data: {e}")
    
    async def monitor_status(self):
        """Monitor heat pump status continuously"""
        self.running = True
        
        while self.running:
            try:
                # Check if we're receiving data
                if self.last_update and (datetime.now() - self.last_update) > timedelta(minutes=5):
                    self.logger.warning("No HeishaMon data received for 5 minutes")
                
                # Perform status checks
                await self._check_system_health()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in status monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _check_system_health(self):
        """Check system health and log warnings"""
        try:
            # Check for error states
            if 'Error' in self.current_status:
                error_code = self.current_status['Error'].get('value', 0)
                if error_code != 0:
                    self.logger.warning(f"Heat pump error code: {error_code}")
            
            # Check temperatures
            outlet_temp = self.get_parameter('Main_Outlet_Temp')
            inlet_temp = self.get_parameter('Main_Inlet_Temp')
            
            if outlet_temp and inlet_temp:
                temp_diff = outlet_temp - inlet_temp
                if temp_diff > 15:  # Unusual temperature difference
                    self.logger.warning(f"High temperature difference: {temp_diff:.1f}°C")
            
            # Check pump frequency
            pump_freq = self.get_parameter('Pump_Freq')
            if pump_freq and pump_freq > 90:
                self.logger.info(f"Heat pump running at high frequency: {pump_freq}%")
                
        except Exception as e:
            self.logger.error(f"Error checking system health: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current heat pump status"""
        status = {
            'timestamp': datetime.now(),
            'connected': self.last_update is not None,
            'last_update': self.last_update,
            'temperatures': {
                'outlet': self.get_parameter('Main_Outlet_Temp'),
                'inlet': self.get_parameter('Main_Inlet_Temp'), 
                'outside': self.get_parameter('Outside_Temp'),
                'room': self.get_parameter('Room_Thermostat_Temp'),
                'target': self.get_parameter('Z1_Heat_Request_Temp')
            },
            'system': {
                'state': self.get_parameter('Heatpump_State'),
                'mode': self.get_parameter('Operating_Mode_State'),
                'pump_frequency': self.get_parameter('Pump_Freq'),
                'compressor_frequency': self.get_parameter('Compressor_Freq'),
                'energy_consumption': self.get_parameter('Energy_Consumption'),
                'energy_production': self.get_parameter('Energy_Production')
            },
            'sensors': self._get_sensor_data()
        }
        
        # Calculate COP if we have the data
        if status['system']['energy_consumption'] and status['system']['energy_production']:
            if status['system']['energy_consumption'] > 0:
                status['system']['cop'] = status['system']['energy_production'] / status['system']['energy_consumption']
        
        return status
    
    def get_parameter(self, param_name: str) -> Optional[float]:
        """Get a specific parameter value"""
        if param_name in self.current_status:
            return self.current_status[param_name].get('value')
        return None
    
    def _get_sensor_data(self) -> Dict[str, float]:
        """Get all sensor data"""
        sensors = {}
        for key, data in self.current_status.items():
            if key.startswith('sensor_'):
                sensor_name = key[7:]  # Remove 'sensor_' prefix
                sensors[sensor_name] = data.get('value')
        return sensors
    
    async def apply_settings(self, settings: Dict[str, Any]):
        """Apply new settings to the heat pump"""
        try:
            # Set target temperature
            if 'target_temperature' in settings:
                await self.set_target_temperature(settings['target_temperature'])
            
            # Set heat pump mode
            if 'mode' in settings:
                await self.set_heat_pump_mode(settings['mode'])
            
            # Set quiet mode
            if 'quiet_mode' in settings:
                await self.set_quiet_mode(settings['quiet_mode'])
            
            # Set defrost mode
            if 'force_defrost' in settings:
                await self.force_defrost()
            
            self.logger.info(f"Applied settings: {settings}")
            
        except Exception as e:
            self.logger.error(f"Failed to apply settings: {e}")
    
    async def set_target_temperature(self, temperature: float):
        """Set target temperature for Zone 1"""
        # Validate temperature range
        if not (15.0 <= temperature <= 30.0):
            self.logger.error(f"Temperature {temperature}°C outside valid range (15-30°C)")
            return
        
        await self.mqtt_client.send_heisha_command('SetZ1HeatRequestTemperature', int(temperature))
        self.logger.info(f"Set target temperature to {temperature}°C")
    
    async def set_heat_pump_mode(self, mode: str):
        """Set heat pump operating mode"""
        mode_mapping = {
            'off': 0,
            'heat': 1,
            'cool': 2,
            'auto': 3
        }
        
        if mode.lower() in mode_mapping:
            mode_value = mode_mapping[mode.lower()]
            await self.mqtt_client.send_heisha_command('SetHeatPump', mode_value)
            self.logger.info(f"Set heat pump mode to {mode}")
        else:
            self.logger.error(f"Invalid heat pump mode: {mode}")
    
    async def set_quiet_mode(self, enabled: bool):
        """Enable or disable quiet mode"""
        value = 1 if enabled else 0
        await self.mqtt_client.send_heisha_command('SetQuietMode', value)
        self.logger.info(f"{'Enabled' if enabled else 'Disabled'} quiet mode")
    
    async def force_defrost(self):
        """Force defrost cycle"""
        await self.mqtt_client.send_heisha_command('SetForceDefrost', 1)
        self.logger.info("Forced defrost cycle")
    
    async def set_holiday_mode(self, enabled: bool):
        """Enable or disable holiday mode"""
        value = 1 if enabled else 0
        await self.mqtt_client.send_heisha_command('SetHolidayMode', value)
        self.logger.info(f"{'Enabled' if enabled else 'Disabled'} holiday mode")
    
    def is_heating_active(self) -> bool:
        """Check if heating is currently active"""
        pump_freq = self.get_parameter('Pump_Freq')
        comp_freq = self.get_parameter('Compressor_Freq')
        
        return (pump_freq and pump_freq > 0) or (comp_freq and comp_freq > 0)
    
    def get_current_cop(self) -> Optional[float]:
        """Get current coefficient of performance"""
        energy_in = self.get_parameter('Energy_Consumption')
        energy_out = self.get_parameter('Energy_Production')
        
        if energy_in and energy_out and energy_in > 0:
            return energy_out / energy_in
        
        return None
    
    def get_system_efficiency(self) -> Dict[str, Any]:
        """Get system efficiency metrics"""
        cop = self.get_current_cop()
        
        return {
            'cop': cop,
            'pump_frequency': self.get_parameter('Pump_Freq'),
            'compressor_frequency': self.get_parameter('Compressor_Freq'),
            'energy_consumption_kw': self.get_parameter('Energy_Consumption'),
            'energy_production_kw': self.get_parameter('Energy_Production'),
            'is_heating': self.is_heating_active(),
            'timestamp': datetime.now()
        }
    
    async def emergency_stop(self):
        """Emergency stop of heat pump"""
        self.logger.warning("Emergency stop activated")
        await self.set_heat_pump_mode('off')
        
    def stop(self):
        """Stop the controller"""
        self.running = False