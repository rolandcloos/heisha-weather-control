# Mitwirkende Guide

Vielen Dank für Ihr Interesse an der Mitwirkung am Heisha Weather Prediction Control Projekt!

## 🚀 Wie Sie beitragen können

### Fehlerberichte (Bug Reports)

Wenn Sie einen Fehler gefunden haben:

1.  **Überprüfen Sie existierende Issues** - Möglicherweise wurde der Fehler bereits berichtet
2.  **Erstellen Sie ein neues Issue** mit folgenden Informationen:
    -   Detaillierte Beschreibung des Problems
    -   Schritte zur Reproduktion
    -   Erwartetes vs. tatsächliches Verhalten
    -   Add-On Version und Home Assistant Version
    -   Relevante Logs (ohne API-Keys!)

### Feature Requests

Für neue Funktionen:

1.  **Diskutieren Sie Ihre Idee** in einem Issue bevor Sie Code schreiben
2.  **Beschreiben Sie den Anwendungsfall** - warum würde das Feature nützlich sein?
3.  **Berücksichtigen Sie Kompatibilität** mit existierenden Funktionen

### Code Beiträge

#### Entwicklungsumgebung einrichten

```bash
# Repository klonengit clone https://github.com/roland/heisha-weather-control.gitcd heisha-weather-control# Entwicklung in VS Code mit Dev Containers (empfohlen)code .# Oder lokale Python-Umgebungpython -m venv venvsource venv/bin/activate  # Linux/Mac# odervenvScriptsactivate     # Windowspip install -r requirements.txt
```

#### Code-Standards

-   **Python 3.9+** kompatibel
-   **PEP 8** Style Guide befolgen
-   **Type Hints** verwenden wo möglich
-   **Docstrings** für alle öffentlichen Funktionen
-   **Async/Await** für I/O-Operationen

#### Pull Request Prozess

1.  **Fork** das Repository
2.  **Erstellen Sie einen Feature Branch**: `git checkout -b feature/amazing-feature`
3.  **Schreiben Sie Tests** für neue Funktionalität
4.  **Commiten Sie Ihre Änderungen**: `git commit -m 'Add amazing feature'`
5.  **Push zum Branch**: `git push origin feature/amazing-feature`
6.  **Öffnen Sie einen Pull Request**

#### Code Review Kriterien

-   Funktionalität arbeitet wie erwartet
-   Code ist gut dokumentiert
-   Tests sind vorhanden und bestehen
-   Keine Breaking Changes ohne Diskussion
-   Performance-Auswirkungen berücksichtigt

## 🧪 Tests

### Unit Tests ausführen

```bash
python -m pytest tests/ -v
```

### Integration Tests

```bash
# Mit Docker Compose für MQTT/HA Simulationdocker-compose -f tests/docker-compose.test.yml uppython -m pytest tests/integration/ -v
```

### Manual Testing

1.  **Home Assistant Testumgebung** aufsetzen
2.  **HeishaMon Simulator** verwenden (siehe `tests/heishamon_simulator.py`)
3.  **Mock Weather Data** für API-unabhängige Tests

## 📚 Dokumentation

### README Updates

-   Halten Sie die **Installation Guide** aktuell
-   **Konfiguration Beispiele** sollten funktionieren
-   **Screenshots** bei UI-Änderungen aktualisieren

### Code Dokumentation

```python
def predict_energy_consumption(self, conditions: Dict[str, Any]) -> Optional[float]:    """    Predict energy consumption based on weather and house conditions.        Args:        conditions: Dictionary with weather and house data                   - outside_temp: Outside temperature in °C                   - target_temp: Desired room temperature in °C                   - humidity: Relative humidity in %                   - wind_speed: Wind speed in m/s                       Returns:        Predicted energy consumption in kW or None if prediction not possible            Raises:        ValueError: If required conditions are missing or invalid    """
```

## 🐛 Debugging

### Logging aktivieren

```yaml
logging:  level: "DEBUG"
```

### Häufige Debug-Schritte

1.  **MQTT Messages** mit `mosquitto_sub` überwachen:

```bash
mosquitto_sub -h localhost -t "panasonic_heat_pump/#" -v
```

2.  **Weather API Calls** testen:

```python
import aiohttp# Test API connectivity
```

3.  **Learning Engine** Status prüfen:

```python
learning_confidence = engine.get_learning_confidence()data_points = len(engine.historical_data)
```

## 🔄 Release Prozess

### Versioning

Wir verwenden [Semantic Versioning](https://semver.org/):

-   **MAJOR**: Breaking Changes
-   **MINOR**: Neue Features (rückwärtskompatibel)
-   **PATCH**: Bugfixes

### Release Checklist

-    Version in `config.yaml` und `config.json` updaten
-    `CHANGELOG.md` aktualisieren
-    Tests bestehen alle
-    Dokumentation ist aktuell
-    Docker Images bauen erfolgreich
-    Tag erstellen: `git tag v1.0.1`
-    Release Notes schreiben

## 💡 Entwicklungs-Tipps

### Machine Learning Komponenten

```python
# Neue Lern-Algorithmen hinzufügenclass YourNewLearningAlgorithm:    def train(self, data):        # Implementierung        pass        def predict(self, inputs):        # Implementierung         pass
```

### Weather Provider hinzufügen

```python
# Neue Wetter-APIs integrierenasync def _fetch_your_provider_current(self, session):    # API-spezifische Implementierung    pass
```

### Predictive Algorithms erweitern

```python
# Neue Vorhersage-Featuresdef _calculate_your_prediction_feature(self, weather_data):    # Algorithmus-Logik    pass
```

## ❓ Hilfe bekommen

### Community Support

-   **GitHub Discussions** für allgemeine Fragen
-   **Issues** für spezifische Probleme
-   **Home Assistant Community Forum** für Integration-Fragen

### Kontakt

-   **Maintainer**: [roland@example.com](mailto:roland@example.com)
-   **Matrix Chat**: `#heisha-weather-control:matrix.org`

## 📜 Code of Conduct

### Unsere Werte

-   **Respektvoller Umgang** mit allen Mitwirkenden
-   **Konstruktives Feedback** geben und empfangen
-   **Inklusive Community** für alle Hintergründe
-   **Fokus auf technische Lösungen** statt persönliche Angriffe

### Inakzeptables Verhalten

-   Diskriminierende oder verletzende Sprache
-   Persönliche Angriffe oder Trolling
-   Spam oder Off-Topic Diskussionen
-   Nicht autorisierte Weitergabe privater Informationen

### Berichterstellung

Verstöße gegen den Code of Conduct melden Sie bitte an: [roland@example.com](mailto:roland@example.com)

## 🏆 Anerkennung

Alle Mitwirkenden werden im `README.md` und in Release Notes erwähnt.

### Hall of Fame

-   **Major Contributors**: Signifikante Feature-Entwicklung
-   **Bug Hunters**: Kritische Fehler gefunden und behoben
-   **Documentation Heroes**: Großartige Dokumentations-Beiträge
-   **Community Champions**: Hilfe bei User Support

Vielen Dank für Ihren Beitrag zur Verbesserung der Wärmepumpen-Effizienz! 🌱