# Heisha Weather Prediction Control

Ein intelligentes Home Assistant Add-On zur Steuerung von Panasonic Wärmepumpen mit HeishaMon über MQTT, integrierter Wettervorhersage und lernendem Algorithmus für optimale Energieeffizienz.

## 🌟 Features

-   **MQTT Integration**: Vollständige Steuerung über HeishaMon
-   **Wettervorhersage**: Integration verschiedener Wetter-APIs (OpenWeatherMap, WeatherAPI, DWD)
-   **Predictive Control**: 24h-Vorhersage für optimale Heizungssteuerung
-   **Lernender Algorithmus**: Automatische Anpassung basierend auf Gebäudeverhalten
-   **Benutzerfreundlich**: Einfache Konfiguration mit Expert-Modus
-   **Gebäudemasse-Berücksichtigung**: Intelligente Trägheitsberechnung für Fußbodenheizung
-   **Solargewinn-Optimierung**: Berücksichtigung von Sonnenstand und Wärmegewinnen

## 📋 Voraussetzungen

### Hardware

-   Panasonic Wärmepumpe (Aquarea-Serie)
-   HeishaMon-Hardware (ESP8266/ESP32 mit CN-CNT Interface)
-   Home Assistant mit Supervisor (HASSIO/HAOS)

### Software

-   Home Assistant Core 2023.1 oder neuer
-   MQTT Broker (Mosquitto Add-On empfohlen)
-   HeishaMon Firmware auf dem ESP-Board

## 🔧 Installation

### Schritt 1: Repository hinzufügen

1.  Öffnen Sie Home Assistant
2.  Gehen Sie zu **Supervisor** → **Add-on Store**
3.  Klicken Sie auf das **⋮** Menü (oben rechts)
4.  Wählen Sie **Repositories**
5.  Fügen Sie diese URL hinzu:
    
    ```
    https://github.com/rolandcloos/heisha-weather-control
    ```

### Schritt 2: Add-On installieren

1.  Suchen Sie nach "Heisha Weather Prediction Control" im Add-on Store
2.  Klicken Sie auf **INSTALL**
3.  Warten Sie, bis die Installation abgeschlossen ist

### Alternative: Lokale Installation

Falls das Repository nicht funktioniert, können Sie eine lokale Installation durchführen:

1.  Verbinden Sie sich per SSH mit Ihrem Home Assistant System
2.  Navigieren Sie zu: `cd /usr/share/hassio/addons/local/`
3.  Klonen Sie das Repository: `git clone https://github.com/rolandcloos/heisha-weather-control.git`
4.  Starten Sie den Supervisor neu
5.  Das Add-on erscheint unter **Lokale Add-ons**

### Schritt 3: MQTT Broker einrichten

Falls noch nicht vorhanden, installieren Sie den Mosquitto MQTT Broker:

1.  Gehen Sie zu **Add-on Store**
2.  Suchen Sie nach "Mosquitto broker"
3.  Installieren und starten Sie ihn
4.  Erstellen Sie einen MQTT-Benutzer unter **Settings** → **People** → **Users**

### Schritt 4: Wetter-API Schlüssel besorgen

#### OpenWeatherMap (empfohlen)

1.  Registrieren Sie sich auf [OpenWeatherMap](https://openweathermap.org/api)
2.  Erstellen Sie einen kostenlosen API-Schlüssel
3.  Notieren Sie sich den API-Key

#### Alternative: WeatherAPI

1.  Registrieren Sie sich auf [WeatherAPI](https://www.weatherapi.com/)
2.  Erhalten Sie Ihren kostenlosen API-Schlüssel

### Schritt 5: HeishaMon konfigurieren

Stellen Sie sicher, dass Ihr HeishaMon richtig konfiguriert ist:

1.  HeishaMon sollte mit Ihrem MQTT Broker verbunden sein
2.  Standard Topics sollten verwendet werden:
    -   `panasonic_heat_pump/main/` (für Hauptdaten)
    -   `panasonic_heat_pump/commands/` (für Befehle)

## ⚙️ Konfiguration

### Basis-Konfiguration (Anfänger-freundlich)

Öffnen Sie die Add-On Konfiguration und passen Sie diese Grundeinstellungen an:

```yaml
mqtt:  broker: "core-mosquitto"  # Ihr MQTT Broker  port: 1883  username: "ihr_mqtt_benutzer"  password: "ihr_mqtt_passwort"  topic_prefix: "panasonic_heat_pump"weather:  api_provider: "openweathermap"  api_key: "IHR_WETTER_API_SCHLUESSEL"  update_interval: 300  # 5 Minutenhouse:  latitude: 50.9375    # Ihre Koordinaten  longitude: 6.9603    # (z.B. Köln)  timezone: "Europe/Berlin"  heating_system_type: "underfloor"  # underfloor, radiator, mixed  building_thermal_mass: "medium"    # low, medium, high  target_temperature: 21.0           # Wunschtemperatur in °C  night_setback: 2.0                 # Nachtabsenkung in K
```

### Erweiterte Konfiguration (Experten)

Für feinere Kontrolle können Sie zusätzliche Parameter anpassen:

```yaml
advanced:  thermal_lag_hours: 4.0           # Trägheit des Heizsystems (Stunden)  solar_gain_factor: 0.3           # Sonnenwärme-Faktor (0-1)  wind_factor: 0.1                 # Windeinfluss-Faktor (0-1)  learning_rate: 0.05              # Lerngeschwindigkeit (0.001-0.5)  prediction_horizon_hours: 24     # Vorhersage-Zeitraum (6-48h)  min_runtime_minutes: 30          # Min. Laufzeit WP (10-120 min)  max_modulation: 100              # Max. Leistung % (20-100)logging:  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
```

## 🏠 Gebäude-Parameter erklärt

### `heating_system_type`

-   **underfloor**: Fußbodenheizung (hohe Trägheit)
-   **radiator**: Heizkörper (niedrige Trägheit)
-   **mixed**: Mischsystem

### `building_thermal_mass`

-   **low**: Leichtbauweise, schnelle Temperaturänderungen
-   **medium**: Standard-Massivbau
-   **high**: Sehr massiver Bau (Beton, Stein), sehr träge

### `solar_gain_factor`

Berücksichtigt passive Solargewinne:

-   **0.1**: Wenige/kleine Fenster, Nordseite
-   **0.3**: Normal (Standard)
-   **0.6**: Viele große Südfenster, Wintergarten

## 🚀 Start und Betrieb

### Schritt 1: Konfiguration speichern

1.  Speichern Sie Ihre Konfiguration
2.  Klicken Sie auf **START**

### Schritt 2: Logs überprüfen

1.  Gehen Sie zum **Log**-Tab
2.  Überprüfen Sie, ob alle Verbindungen erfolgreich sind:
    
    ```
    [INFO] MQTT connected successfully[INFO] Weather API connection established[INFO] HeishaMon device detected[INFO] Starting predictive control loop
    ```
    

### Schritt 3: Home Assistant Integration

Das Add-On erstellt automatisch diese Entitäten in Home Assistant:

-   `sensor.heisha_current_temp`: Aktuelle Temperatur
-   `sensor.heisha_target_temp`: Ziel-Temperatur
-   `sensor.heisha_weather_prediction`: Wettervorhersage
-   `climate.heisha_heat_pump`: Klimasteuerung
-   `switch.heisha_learning_mode`: Lernmodus ein/aus

## 📊 Überwachung und Dashboards

### Empfohlenes Dashboard

Erstellen Sie ein Dashboard mit folgenden Karten:

1.  **Thermostat-Karte** für `climate.heisha_heat_pump`
2.  **Verlaufs-Diagramm** für Temperaturverläufe
3.  **Wetter-Karte** für die Vorhersage
4.  **Gauge-Karten** für Effizienz-Metriken

### Wichtige Sensoren

-   `sensor.heisha_efficiency`: Aktuelle COP (Coefficient of Performance)
-   `sensor.heisha_energy_today`: Heutiger Energieverbrauch
-   `sensor.heisha_prediction_accuracy`: Genauigkeit der Vorhersagen
-   `sensor.heisha_learning_progress`: Lern-Fortschritt

## 🧠 Wie das Lernsystem funktioniert

### Datensammlung

Das System sammelt kontinuierlich Daten:

-   Innen- und Außentemperaturen
-   Wetter-Parameter (Wind, Sonne, Luftfeuchtigkeit)
-   WP-Betriebsdaten (Vorlauf, Rücklauf, Leistung)
-   Benutzer-Eingriffe und -Präferenzen

### Lern-Algorithmus

-   **Thermal Response Learning**: Lernt, wie schnell Ihr Gebäude auf Heizung reagiert
-   **Weather Impact Learning**: Erkennt Wettereinflüsse auf den Heizbedarf
-   **Efficiency Optimization**: Findet optimale Betriebsparameter für maximale Effizienz

### Anpassung über Zeit

-   **Woche 1-2**: Grundlegende Kalibrierung
-   **Monat 1**: Saisonale Anpassungen
-   **Nach 3 Monaten**: Vollständig optimierte Steuerung

## 🔧 Fehlerbehebung

### Häufige Probleme

#### MQTT Verbindung fehlgeschlagen

```
[ERROR] Failed to connect to MQTT broker
```

**Lösung**:

-   Prüfen Sie MQTT Broker-Einstellungen
-   Überprüfen Sie Benutzername/Passwort
-   Stellen Sie sicher, dass der Broker läuft

#### Wetter-API Fehler

```
[ERROR] Weather API authentication failed
```

**Lösung**:

-   Überprüfen Sie Ihren API-Schlüssel
-   Prüfen Sie API-Limits (kostenlose Accounts haben Grenzen)
-   Wechseln Sie ggf. den API-Provider

#### HeishaMon nicht gefunden

```
[WARNING] No HeishaMon data received
```

**Lösung**:

-   Überprüfen Sie HeishaMon-Hardware
-   Prüfen Sie MQTT-Topics im HeishaMon
-   Stellen Sie sicher, dass `topic_prefix` korrekt ist

### Debug-Modus aktivieren

Für detaillierte Diagnose:

```yaml
logging:  level: "DEBUG"
```

Dies zeigt alle internen Berechnungen und Entscheidungen.

## 📈 Optimierung und Tipps

### Effizienz maximieren

1.  **Lassen Sie das System 2-4 Wochen lernen** bevor Sie größere Anpassungen vornehmen
2.  **Überwachen Sie die COP-Werte** - sie sollten sich mit der Zeit verbessern
3.  **Nutzen Sie Wettervorhersagen** - das System plant 24h im Voraus
4.  **Vermeiden Sie häufige manuelle Eingriffe** während der Lernphase

### Erweiterte Anpassungen

Für erfahrene Benutzer:

```yaml
advanced:  # Für träge Systeme (dicke Estriche, hohe Masse)  thermal_lag_hours: 6.0    # Für Häuser mit vielen Südfenstern  solar_gain_factor: 0.5    # Für windexponierte Lagen  wind_factor: 0.15    # Schnelleres Lernen (Vorsicht: kann zu Instabilität führen)  learning_rate: 0.1
```

## 🔄 Updates

Das Add-On prüft automatisch auf Updates. Sie werden in Home Assistant benachrichtigt, wenn neue Versionen verfügbar sind.

### Manuelle Updates

1.  Gehen Sie zu **Supervisor** → **Add-on Store**
2.  Suchen Sie nach "Heisha Weather Prediction Control"
3.  Klicken Sie auf **UPDATE**, falls verfügbar

## 🆘 Support

### Community Support

-   **Home Assistant Community**: [Diskussion](https://community.home-assistant.io/)
-   **GitHub Issues**: [Problem melden](https://github.com/roland/heisha-weather-control/issues)

### Logs für Support

Bei Problemen fügen Sie diese Informationen hinzu:

1.  Add-On Logs (letzten 50 Zeilen)
2.  Ihre Konfiguration (ohne API-Schlüssel!)
3.  Home Assistant Version
4.  HeishaMon Version

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

## 🤝 Mitwirkende

Beiträge sind willkommen! Bitte lesen Sie [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

## ⭐ Danksagungen

-   **HeishaMon Team** für die exzellente Hardware-Integration
-   **Home Assistant Community** für Feedback und Testing
-   **OpenWeatherMap** für die zuverlässige Wetter-API

---

**Version**: 1.0.0  
**Letzte Aktualisierung**: September 2024  
**Kompatibilität**: Home Assistant 2023.1+