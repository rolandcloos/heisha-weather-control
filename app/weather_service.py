"""
Weather Service for Heisha Weather Prediction Control
Handles weather data retrieval from various APIs
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import aiohttp
import json

from astral import LocationInfo
from astral.sun import sun


class WeatherService:
    """Weather service supporting multiple weather APIs"""
    
    def __init__(self, provider: str, api_key: str, latitude: float, 
                 longitude: float, update_interval: int = 300):
        self.logger = logging.getLogger(__name__)
        self.provider = provider.lower()
        self.api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.update_interval = update_interval
        
        self.current_weather = {}
        self.forecast_data = []
        self.running = False
        
        # Setup location for solar calculations
        self.location = LocationInfo(
            name="Home",
            region="Local", 
            timezone="UTC",
            latitude=latitude,
            longitude=longitude
        )
        
        # API configurations
        self.api_configs = {
            'openweathermap': {
                'base_url': 'https://api.openweathermap.org/data/2.5',
                'current_endpoint': '/weather',
                'forecast_endpoint': '/forecast'
            },
            'weatherapi': {
                'base_url': 'https://api.weatherapi.com/v1',
                'current_endpoint': '/current.json',
                'forecast_endpoint': '/forecast.json'
            }
        }
        
    async def initialize(self) -> bool:
        """Initialize weather service"""
        if not self.api_key:
            self.logger.warning("No weather API key provided - using mock data")
            return True
            
        try:
            # Test API connection
            async with aiohttp.ClientSession() as session:
                current_data = await self._fetch_current_weather(session)
                if current_data:
                    self.logger.info(f"Weather service initialized with {self.provider}")
                    return True
                else:
                    self.logger.error("Failed to fetch initial weather data")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to initialize weather service: {e}")
            return False
    
    async def start_updates(self):
        """Start periodic weather updates"""
        self.running = True
        while self.running:
            try:
                await self._update_weather_data()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                self.logger.error(f"Error updating weather data: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute
    
    async def stop(self):
        """Stop weather updates"""
        self.running = False
    
    async def _update_weather_data(self):
        """Update current weather and forecast data"""
        if not self.api_key:
            self._generate_mock_data()
            return
            
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch current weather
                current_data = await self._fetch_current_weather(session)
                if current_data:
                    self.current_weather = current_data
                    
                # Fetch forecast
                forecast_data = await self._fetch_forecast(session)
                if forecast_data:
                    self.forecast_data = forecast_data
                    
            self.logger.debug("Weather data updated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to update weather data: {e}")
    
    async def _fetch_current_weather(self, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
        """Fetch current weather data"""
        if self.provider == 'openweathermap':
            return await self._fetch_openweathermap_current(session)
        elif self.provider == 'weatherapi':
            return await self._fetch_weatherapi_current(session)
        else:
            self.logger.error(f"Unsupported weather provider: {self.provider}")
            return None
    
    async def _fetch_forecast(self, session: aiohttp.ClientSession) -> Optional[List[Dict[str, Any]]]:
        """Fetch weather forecast data"""
        if self.provider == 'openweathermap':
            return await self._fetch_openweathermap_forecast(session)
        elif self.provider == 'weatherapi':
            return await self._fetch_weatherapi_forecast(session)
        else:
            self.logger.error(f"Unsupported weather provider: {self.provider}")
            return None
    
    async def _fetch_openweathermap_current(self, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
        """Fetch current weather from OpenWeatherMap"""
        try:
            config = self.api_configs['openweathermap']
            url = f"{config['base_url']}{config['current_endpoint']}"
            
            params = {
                'lat': self.latitude,
                'lon': self.longitude,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        'temperature': data['main']['temp'],
                        'humidity': data['main']['humidity'],
                        'pressure': data['main']['pressure'],
                        'wind_speed': data.get('wind', {}).get('speed', 0),
                        'wind_direction': data.get('wind', {}).get('deg', 0),
                        'clouds': data.get('clouds', {}).get('all', 0),
                        'visibility': data.get('visibility', 10000) / 1000,  # Convert to km
                        'description': data['weather'][0]['description'],
                        'timestamp': datetime.now()
                    }
                else:
                    self.logger.error(f"OpenWeatherMap API error: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch OpenWeatherMap current data: {e}")
            return None
    
    async def _fetch_openweathermap_forecast(self, session: aiohttp.ClientSession) -> Optional[List[Dict[str, Any]]]:
        """Fetch forecast from OpenWeatherMap"""
        try:
            config = self.api_configs['openweathermap']
            url = f"{config['base_url']}{config['forecast_endpoint']}"
            
            params = {
                'lat': self.latitude,
                'lon': self.longitude,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    forecast = []
                    for item in data['list'][:24]:  # Next 24 hours (3-hour intervals)
                        forecast.append({
                            'timestamp': datetime.fromtimestamp(item['dt']),
                            'temperature': item['main']['temp'],
                            'humidity': item['main']['humidity'],
                            'pressure': item['main']['pressure'],
                            'wind_speed': item.get('wind', {}).get('speed', 0),
                            'wind_direction': item.get('wind', {}).get('deg', 0),
                            'clouds': item.get('clouds', {}).get('all', 0),
                            'description': item['weather'][0]['description']
                        })
                    
                    return forecast
                else:
                    self.logger.error(f"OpenWeatherMap forecast API error: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch OpenWeatherMap forecast: {e}")
            return None
    
    async def _fetch_weatherapi_current(self, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
        """Fetch current weather from WeatherAPI"""
        try:
            config = self.api_configs['weatherapi']
            url = f"{config['base_url']}{config['current_endpoint']}"
            
            params = {
                'key': self.api_key,
                'q': f"{self.latitude},{self.longitude}",
                'aqi': 'no'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    current = data['current']
                    
                    return {
                        'temperature': current['temp_c'],
                        'humidity': current['humidity'],
                        'pressure': current['pressure_mb'],
                        'wind_speed': current['wind_kph'] / 3.6,  # Convert to m/s
                        'wind_direction': current['wind_degree'],
                        'clouds': current['cloud'],
                        'visibility': current['vis_km'],
                        'description': current['condition']['text'],
                        'timestamp': datetime.now()
                    }
                else:
                    self.logger.error(f"WeatherAPI error: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch WeatherAPI current data: {e}")
            return None
    
    async def _fetch_weatherapi_forecast(self, session: aiohttp.ClientSession) -> Optional[List[Dict[str, Any]]]:
        """Fetch forecast from WeatherAPI"""
        try:
            config = self.api_configs['weatherapi']
            url = f"{config['base_url']}{config['forecast_endpoint']}"
            
            params = {
                'key': self.api_key,
                'q': f"{self.latitude},{self.longitude}",
                'days': 2,  # Today + tomorrow
                'aqi': 'no',
                'alerts': 'no'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    forecast = []
                    for day in data['forecast']['forecastday']:
                        for hour in day['hour']:
                            if datetime.fromtimestamp(hour['time_epoch']) > datetime.now():
                                forecast.append({
                                    'timestamp': datetime.fromtimestamp(hour['time_epoch']),
                                    'temperature': hour['temp_c'],
                                    'humidity': hour['humidity'],
                                    'pressure': hour['pressure_mb'],
                                    'wind_speed': hour['wind_kph'] / 3.6,  # Convert to m/s
                                    'wind_direction': hour['wind_degree'],
                                    'clouds': hour['cloud'],
                                    'description': hour['condition']['text']
                                })
                                
                                if len(forecast) >= 24:  # Limit to 24 hours
                                    break
                        
                        if len(forecast) >= 24:
                            break
                    
                    return forecast
                else:
                    self.logger.error(f"WeatherAPI forecast error: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch WeatherAPI forecast: {e}")
            return None
    
    def _generate_mock_data(self):
        """Generate mock weather data for testing"""
        now = datetime.now()
        
        # Generate realistic mock current weather
        self.current_weather = {
            'temperature': 8.5,
            'humidity': 65,
            'pressure': 1013.25,
            'wind_speed': 3.2,
            'wind_direction': 225,
            'clouds': 40,
            'visibility': 10.0,
            'description': 'partly cloudy',
            'timestamp': now
        }
        
        # Generate mock forecast
        self.forecast_data = []
        for i in range(24):
            self.forecast_data.append({
                'timestamp': now + timedelta(hours=i),
                'temperature': 8.5 + (i * 0.2) - (i > 12 and (i - 12) * 0.3 or 0),
                'humidity': 65 + (i % 5 - 2) * 5,
                'pressure': 1013.25 + (i % 7 - 3),
                'wind_speed': 3.2 + (i % 3) * 0.5,
                'wind_direction': 225,
                'clouds': 40 + (i % 4) * 10,
                'description': 'partly cloudy'
            })
    
    async def get_current_weather(self) -> Dict[str, Any]:
        """Get current weather data"""
        return self.current_weather
    
    async def get_forecast(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get weather forecast for specified hours"""
        return self.forecast_data[:hours]
    
    def calculate_solar_radiation(self, timestamp: datetime, cloud_cover: float) -> float:
        """Calculate solar radiation based on sun position and cloud cover"""
        try:
            s = sun(self.location.observer, date=timestamp.date())
            
            # Check if sun is up
            if timestamp.time() < s['sunrise'].time() or timestamp.time() > s['sunset'].time():
                return 0.0
            
            # Calculate sun elevation (simplified)
            from astral.sun import elevation
            sun_elevation = elevation(self.location.observer, timestamp)
            
            if sun_elevation <= 0:
                return 0.0
            
            # Maximum theoretical solar radiation (simplified)
            max_radiation = 1000  # W/m²
            
            # Adjust for sun elevation
            elevation_factor = sin(radians(sun_elevation)) if sun_elevation > 0 else 0
            
            # Adjust for cloud cover
            cloud_factor = 1.0 - (cloud_cover / 100.0 * 0.8)
            
            radiation = max_radiation * elevation_factor * cloud_factor
            
            return max(0, radiation)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate solar radiation: {e}")
            return 0.0
    
    def get_weather_summary(self) -> Dict[str, Any]:
        """Get summary of current weather conditions"""
        if not self.current_weather:
            return {}
        
        current = self.current_weather
        
        # Calculate solar radiation
        solar_radiation = self.calculate_solar_radiation(
            current['timestamp'], 
            current.get('clouds', 0)
        )
        
        return {
            'outside_temperature': current.get('temperature', 0),
            'humidity': current.get('humidity', 50),
            'wind_speed': current.get('wind_speed', 0),
            'cloud_cover': current.get('clouds', 0),
            'solar_radiation': solar_radiation,
            'weather_description': current.get('description', 'unknown'),
            'timestamp': current.get('timestamp', datetime.now())
        }


def sin(angle_rad: float) -> float:
    """Calculate sine of angle in radians"""
    import math
    return math.sin(angle_rad)

def radians(angle_deg: float) -> float:
    """Convert degrees to radians"""
    import math
    return math.radians(angle_deg)