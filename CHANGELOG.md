# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),und dieses Projekt hält sich an [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unveröffentlicht]

## [1.0.0] - 2024-09-24

### Hinzugefügt

-   **Vollständige MQTT Integration** mit HeishaMon
    
    -   Automatische Erkennung von Panasonic Wärmepumpen
    -   Bidirektionale Kommunikation für Steuerung und Status
    -   Home Assistant Auto-Discovery
-   **Multi-Provider Wetter-APIs**
    
    -   OpenWeatherMap Integration (empfohlen)
    -   WeatherAPI Support
    -   Automatisches Fallback auf Mock-Daten für Tests
    -   24h-Wettervorhersage mit stündlicher Auflösung
-   **Intelligente Predictive Control**
    
    -   24h-Vorhersage-Algorithmus
    -   Berücksichtigung von Gebäude-Trägheit
    -   Solare Wärmegewinne und Windverluste
    -   Proaktive Temperaturregelung
-   **Lernender Algorithmus**
    
    -   Machine Learning mit Random Forest
    -   Automatische Anpassung der Systemparameter
    -   COP-Optimierung basierend auf Verhalten
    -   Kontinuierliche Verbesserung der Vorhersagegenauigkeit
-   **Benutzerfreundliche Konfiguration**
    
    -   Einfacher Basis-Modus für Anfänger
    -   Erweiterte Einstellungen für Experten
    -   Validierung aller Eingabeparameter
    -   Geografische Koordinaten mit Zeitzonenunterstützung
-   **Gebäude-spezifische Anpassungen**
    
    -   Fußbodenheizung vs. Heizkörper-Unterstützung
    -   Verschiedene Gebäudemasse-Profile (leicht/mittel/schwer)
    -   Anpassbare Nachtabsenkung
    -   Solargewinn-Konfiguration basierend auf Ausrichtung
-   **Umfassendes Monitoring**
    
    -   Echtzeit-Effizienz-Metriken (COP)
    -   Energieverbrauchs-Tracking
    -   Vorhersage-Genauigkeits-Monitoring
    -   Lern-Fortschritts-Anzeige
-   **Home Assistant Integration**
    
    -   Automatische Entity-Erstellung
    -   Climate-Control Entity
    -   Sensor-Entities für alle wichtigen Metriken
    -   Dashboard-freundliche Attribute

### Technische Details

-   **Async/Await Architecture** für optimale Performance
-   **Fehlerbehandlung** mit automatischen Wiederherstellungsversuchen
-   **Daten-Persistierung** für Lern-Algorithmen
-   **Logging** mit konfigurierbaren Levels
-   **Docker-basierte** Bereitstellung

### Sicherheit

-   Sichere Passwort-Behandlung in MQTT
-   API-Key-Schutz für Wetter-Services
-   Keine Weitergabe sensibler Daten

### Performance

-   Optimierte Algorithmen für Embedded-Systeme
-   Minimaler Speicherverbrauch durch Datenrotation
-   Effiziente MQTT-Kommunikation

### Kompatibilität

-   Home Assistant 2023.1+
-   HeishaMon alle aktuellen Versionen
-   Panasonic Aquarea-Serie (alle Modelle mit CN-CNT)
-   Multi-Architektur Support (ARM32/64, x86, x64)