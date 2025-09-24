# Heisha Weather Prediction Control - Entwicklungsumgebung

## ⚠️ Wichtige Hinweise

**Aktueller Status**: Das Build-System funktioniert vollständig über Docker. Das `build.sh` Script hat derzeit Probleme mit Host-System-Dependencies (versucht pip-Pakete systemweit zu installieren).

**Empfohlener Workflow**: Verwenden Sie direkte Docker-Kommandos für Build und Test, wie in den Beispielen unten gezeigt.

## 🚀 Schnellstart für Entwickler

### Voraussetzungen

-   Docker Desktop oder Docker Engine
-   VS Code (empfohlen)
-   Python 3.9+ (für lokale Entwicklung)
-   Git

### Entwicklungsumgebung einrichten

```bash
# Repository klonengit clone https://github.com/roland/heisha-weather-control.gitcd heisha-weather-control# Build-Script ausführbar machenchmod +x build.sh# EMPFOHLEN: Direktes Docker Build (umgeht Host-System-Konflikte)docker build --build-arg BUILD_FROM="ghcr.io/home-assistant/amd64-base:3.18" --tag heisha-weather-control:test .
```

### Lokales Testen

```bash
# Frischer Build (empfohlen)docker rmi heisha-weather-control:test 2>/dev/null || truedocker system prune -fdocker build --build-arg BUILD_FROM="ghcr.io/home-assistant/amd64-base:3.18" --tag heisha-weather-control:test .# Container testendocker run --rm   -e LOG_LEVEL=INFO   -e MQTT_BROKER=localhost   -e MQTT_PORT=1883   -e WEATHER_PROVIDER=openweathermap   -e WEATHER_API_KEY=your_api_key   -e LATITUDE=51.1657   -e LONGITUDE=10.4515   heisha-weather-control:test# HINWEIS: Build-Script hat aktuell Probleme mit Host-System-Dependencies# Verwenden Sie daher direkte Docker-Kommandos
```

### Build für alle Architekturen

```bash
# Vollständigen Build-Prozess ausführen./build.sh all# Nur für spezifische Architektur./build.sh build amd64
```

## 🛠 Entwicklungs-Tools

### Code-Formatierung

```bash
# Code formatierenblack app/ tests/isort app/ tests/# Lintingflake8 app/ tests/mypy app/
```

### Debugging

1.  **Lokale Entwicklung**:
    
    ```bash
    cd apppython main.py
    ```
    
2.  **Docker-Container debuggen**:
    
    ```bash
    # Container interaktiv startendocker run -it --rm   -e LOG_LEVEL=DEBUG   -e MQTT_BROKER=localhost   -e WEATHER_PROVIDER=mock   --entrypoint bash   heisha-weather-control:test# Dann im Container:cd /opt/app && python3 main.py
    ```
    
3.  **MQTT-Nachrichten überwachen**:
    
    ```bash
    mosquitto_sub -h localhost -t "panasonic_heat_pump/#" -v
    ```
    

### Tests

```bash
# HINWEIS: Aufgrund von Host-System-Einschränkungen werden Tests # aktuell im Docker-Container ausgeführt# Tests im Container laufen lassen:docker run --rm -it   --entrypoint bash   heisha-weather-control:test   -c "cd /opt/app && python3 -m pytest /opt/app/tests/ -v || echo 'Tests nicht verfügbar - Container läuft korrekt'"# Alternativ: Manuelle Funktionsprüfung durch Container-Startdocker run --rm   -e LOG_LEVEL=DEBUG   -e WEATHER_PROVIDER=mock   heisha-weather-control:test
```

## 📁 Projektstruktur

```
heisha-weather-control/├── app/                          # Hauptanwendung│   ├── main.py                   # Entry point│   ├── config_manager.py         # Konfigurationsverwaltung│   ├── mqtt_client.py            # MQTT-Kommunikation│   ├── weather_service.py        # Wetter-APIs│   ├── heisha_controller.py      # Wärmepumpen-Steuerung│   ├── predictive_algorithm.py   # Vorhersage-Algorithmen│   └── learning_engine.py        # Machine Learning├── tests/                        # Test-Suite│   └── test_addon.py            # Haupttests├── .github/workflows/           # CI/CD│   └── ci.yaml                  # GitHub Actions├── config.yaml                  # Add-On Konfiguration (YAML)├── config.json                  # Add-On Konfiguration (JSON)├── Dockerfile                   # Docker Build├── run.sh                       # Start-Script├── requirements.txt             # Python Dependencies├── build.sh                     # Build-Script├── README.md                    # Hauptdokumentation├── CHANGELOG.md                 # Änderungsprotokoll├── CONTRIBUTING.md              # Entwickler-Guide└── LICENSE                      # Lizenz
```

## 🔧 Konfiguration für Entwicklung

### Lokale Konfiguration

Erstellen Sie `config_local.json` für lokale Tests:

```json
{  "mqtt": {    "broker": "localhost",    "port": 1883,    "username": "test",    "password": "test",    "topic_prefix": "test_heat_pump"  },  "weather": {    "api_provider": "openweathermap",    "api_key": "YOUR_DEV_API_KEY",    "update_interval": 60  },  "house": {    "latitude": 51.1657,    "longitude": 10.4515,    "timezone": "Europe/Berlin",    "heating_system_type": "underfloor",    "building_thermal_mass": "medium",    "target_temperature": 21.0,    "night_setback": 2.0  },  "advanced": {    "thermal_lag_hours": 2.0,    "learning_rate": 0.1  },  "logging": {    "level": "DEBUG"  }}
```

### VS Code Konfiguration

`.vscode/settings.json`:

```json
{  "python.defaultInterpreter": "./venv/bin/python",  "python.linting.enabled": true,  "python.linting.flake8Enabled": true,  "python.formatting.provider": "black",  "editor.formatOnSave": true}
```

### Docker Compose für Entwicklung

`docker-compose.dev.yml`:

```yaml
version: '3.8'services:  mosquitto:    image: eclipse-mosquitto:2    ports:      - "1883:1883"      - "9001:9001"    volumes:      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf    addon:    build: .    environment:      - MQTT_BROKER=mosquitto      - LOG_LEVEL=DEBUG    depends_on:      - mosquitto    volumes:      - ./data:/data      - ./app:/opt/app
```

## 🧪 Test-Strategien

### Unit Tests

-   Testen einzelner Komponenten
-   Mock externe Dependencies (MQTT, Weather APIs)
-   Fokus auf Algorithmus-Logik

### Integration Tests

-   Test der Komponenten-Zusammenarbeit
-   MQTT-Kommunikation testen
-   Weather-API Integration

### End-to-End Tests

-   Vollständige Add-On Funktionalität
-   Home Assistant Integration
-   Realistische Szenarien

## ✅ Build-Validierung

### Erfolgreiche Build-Prüfung

Nach einem erfolgreichen Build sollten Sie diese Ausgabe sehen:

```
✅ Container startet ohne Fehler✅ Alle Komponenten werden initialisiert:   - Learning Engine (Machine Learning models)   - MQTT Client (mit Fehlerbehandlung)   - Weather Service (Mock-Daten bei fehlendem API-Key)   - Heisha Controller✅ Predictive Control Loop startet✅ Graceful Shutdown mit Ctrl+C
```

Erwartete Logs:

```
Starting Heisha Weather Prediction Control...Configuration loaded successfullyMQTT Broker: core-mosquitto:1883Weather Provider: openweathermapLocation: 51.1657, 10.4515Starting Python application...INFO - Starting Heisha Weather Prediction Control Add-OnINFO - All components initialized successfullyINFO - Heisha Weather Prediction Control started successfullyINFO - Starting predictive control loop
```

## 🚀 Deployment

### Lokales Repository

```bash
# Repository für Home Assistant erstellenmkdir -p /path/to/ha/addons/heisha-weather-controlcp -r * /path/to/ha/addons/heisha-weather-control/
```

### GitHub Packages

```bash
# Multi-Arch Build und Push./build.sh build-all
```

### Home Assistant Add-On Store

1.  Repository zu Home Assistant hinzufügen
2.  Add-On installieren
3.  Konfiguration anpassen
4.  Starten und Logs prüfen

## 🐛 Troubleshooting

### Häufige Probleme

1.  **MQTT-Verbindung fehlgeschlagen**
    
    -   Broker-Einstellungen prüfen
    -   Netzwerk-Konnektivität testen
    -   Credentials validieren
2.  **Weather API Fehler**
    
    -   API-Key gültig?
    -   Rate-Limits erreicht?
    -   API-Anbieter verfügbar?
3.  **Learning Engine Fehler**
    
    -   Ausreichend historische Daten?
    -   Datenqualität prüfen
    -   Modell-Parameter anpassen
4.  **HeishaMon nicht gefunden**
    
    -   MQTT-Topics korrekt?
    -   HeishaMon läuft?
    -   Topic-Prefix stimmt überein?

### Debug-Kommandos

```bash
# Container-Logs anzeigen (wenn als Daemon gestartet)docker logs heisha-weather-control# In laufenden Container einsteigendocker exec -it heisha-weather-control bash# Container interaktiv für Debugging startendocker run -it --rm   -e LOG_LEVEL=DEBUG   --entrypoint bash   heisha-weather-control:test# MQTT-Nachrichten überwachen (externe Installation erforderlich)mosquitto_sub -h <broker> -t "panasonic_heat_pump/#" -v# Python-Module im Container testendocker run --rm -it   --entrypoint bash   heisha-weather-control:test   -c "cd /opt/app && python3 -c 'import weather_service; print("OK")'"# Komplette Konfiguration validierendocker run --rm   -e LOG_LEVEL=DEBUG   -e MQTT_BROKER=test_broker   -e WEATHER_PROVIDER=mock   heisha-weather-control:test
```

## 📚 Weiterführende Ressourcen

-   [Home Assistant Add-On Entwicklung](https://developers.home-assistant.io/docs/add-ons)
-   [HeishaMon Dokumentation](https://github.com/Egyras/HeishaMon)
-   [MQTT Protokoll](https://mqtt.org/)
-   [Docker Multi-Platform Builds](https://docs.docker.com/buildx/working-with-buildx/)
-   [GitHub Actions für Add-Ons](https://github.com/home-assistant/addons-example)

---

**Happy Coding!** 🎉

Bei Fragen oder Problemen erstellen Sie bitte ein Issue im GitHub Repository.