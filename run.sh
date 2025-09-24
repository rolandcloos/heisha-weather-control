#!/bin/bash

# Enable strict error handling
set -e

echo "Starting Heisha Weather Prediction Control..."

# Function to read from options.json if available
get_option() {
    local key="$1"
    local default="$2"
    
    # Try to read from options.json if it exists
    if [ -f "/data/options.json" ] && command -v jq >/dev/null 2>&1; then
        local value=$(jq -r ".$key // empty" /data/options.json 2>/dev/null)
        if [ -n "$value" ] && [ "$value" != "null" ]; then
            echo "$value"
            return
        fi
    fi
    
    echo "$default"
}

# Get configuration with environment variable fallbacks
MQTT_BROKER="${MQTT_BROKER:-$(get_option 'mqtt.broker' 'core-mosquitto')}"
MQTT_PORT="${MQTT_PORT:-$(get_option 'mqtt.port' '1883')}"
MQTT_USERNAME="${MQTT_USERNAME:-$(get_option 'mqtt.username' '')}"
MQTT_PASSWORD="${MQTT_PASSWORD:-$(get_option 'mqtt.password' '')}"
TOPIC_PREFIX="${TOPIC_PREFIX:-$(get_option 'mqtt.topic_prefix' 'panasonic_heat_pump')}"

WEATHER_PROVIDER="${WEATHER_PROVIDER:-$(get_option 'weather.api_provider' 'openweathermap')}"
WEATHER_API_KEY="${WEATHER_API_KEY:-$(get_option 'weather.api_key' '')}"
WEATHER_UPDATE_INTERVAL="${WEATHER_UPDATE_INTERVAL:-$(get_option 'weather.update_interval' '300')}"

LATITUDE="${LATITUDE:-$(get_option 'house.latitude' '51.1657')}"
LONGITUDE="${LONGITUDE:-$(get_option 'house.longitude' '10.4515')}"
TIMEZONE="${TIMEZONE:-$(get_option 'house.timezone' 'Europe/Berlin')}"

LOG_LEVEL="${LOG_LEVEL:-$(get_option 'logging.level' 'INFO')}"

# Export environment variables for Python app
export MQTT_BROKER
export MQTT_PORT
export MQTT_USERNAME
export MQTT_PASSWORD
export TOPIC_PREFIX
export WEATHER_PROVIDER
export WEATHER_API_KEY
export WEATHER_UPDATE_INTERVAL
export LATITUDE
export LONGITUDE
export TIMEZONE
export LOG_LEVEL
export CONFIG_FILE="/data/options.json"

echo "Configuration loaded successfully"
echo "MQTT Broker: ${MQTT_BROKER}:${MQTT_PORT}"
echo "Weather Provider: ${WEATHER_PROVIDER}"
echo "Location: ${LATITUDE}, ${LONGITUDE}"

# Run the Python application
echo "Starting Python application..."
cd /opt/app
exec python3 -u main.py