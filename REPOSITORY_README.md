# Heisha Weather Prediction Control - Home Assistant Add-ons Repository

Dieses Repository enthält Home Assistant Add-ons für die intelligente Steuerung von Panasonic Wärmepumpen mit HeishaMon.

## 📦 Verfügbare Add-ons

### Heisha Weather Prediction Control

Intelligente Panasonic Wärmepumpen-Steuerung mit Wettervorhersage und lernendem Algorithmus für optimale Energieeffizienz.

**Features:**
- 🌡️ MQTT Integration mit HeishaMon
- 🌤️ Wettervorhersage-Integration (OpenWeatherMap, WeatherAPI)
- 🧠 Lernender Algorithmus für automatische Optimierung
- 📊 Predictive Control mit 24h-Vorhersage
- 🏠 Gebäudemasse-Berücksichtigung
- ☀️ Solargewinn-Optimierung

## 🚀 Installation

### Methode 1: Add-on Repository hinzufügen

1. Öffnen Sie Home Assistant
2. Gehen Sie zu **Supervisor** → **Add-on Store**
3. Klicken Sie auf das **⋮** Menü (oben rechts)
4. Wählen Sie **Repositories**
5. Fügen Sie diese URL hinzu:
   ```
   https://github.com/rolandcloos/heisha-weather-control
   ```
6. Suchen Sie nach "Heisha Weather Prediction Control"
7. Klicken Sie auf **INSTALL**

### Methode 2: Lokale Installation

Detaillierte Anweisungen finden Sie in der [Add-on Dokumentation](heisha-weather-control/README.md).

## 🔧 Konfiguration

Nach der Installation konfigurieren Sie das Add-on mit Ihren:
- MQTT Broker-Einstellungen
- Wetter-API Schlüssel
- Gebäude-Parametern
- HeishaMon-Einstellungen

Vollständige Konfigurationsanleitung: [Dokumentation](heisha-weather-control/README.md)

## 📋 Voraussetzungen

- Home Assistant mit Supervisor
- Panasonic Wärmepumpe (Aquarea-Serie)
- HeishaMon Hardware (ESP8266/ESP32)
- MQTT Broker (Mosquitto empfohlen)

## 🆘 Support

- **GitHub Issues**: [Problem melden](https://github.com/rolandcloos/heisha-weather-control/issues)
- **Home Assistant Community**: [Diskussion](https://community.home-assistant.io/)
- **Dokumentation**: [Vollständige Anleitung](heisha-weather-control/README.md)

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details.

---

**Maintainer**: Roland Cloos  
**Repository**: https://github.com/rolandcloos/heisha-weather-control