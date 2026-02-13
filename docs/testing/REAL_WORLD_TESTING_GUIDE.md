# Real-World Testing Guide

## Übersicht

Dieser Guide erklärt, wie man die Buch-Erkennungspipeline mit echten Buchfotos testet. Das [`test_real_world_books.py`](../../test_real_world_books.py) Script führt end-to-end Tests durch und validiert die komplette Pipeline.

## 📸 Buchfotografie Best Practices

### Welche Bereiche fotografieren?

Für optimale Ergebnisse fotografiere folgende Bereiche:

1. **Cover (Front)** - Vollständiges Buchcover
   - Titel deutlich sichtbar
   - Autor-Name
   - Cover-Artwork

2. **Rücken (Spine)** - Buchrücken
   - ISBN-Barcode (falls vorhanden)
   - Titel und Autor
   - Verlag

3. **Rückseite** - ISBN-Bereich
   - ISBN-Barcode
   - Preisinformationen
   - Kurzbeschreibung

4. **Innenseite** (optional) - Impressum
   - Vollständige ISBN
   - Verlagsinformationen
   - Erscheinungsjahr

### Fotografie-Tipps

#### ✅ Gute Beleuchtung
- **Natürliches Licht**: Am besten bei Tageslicht fotografieren
- **Gleichmäßige Ausleuchtung**: Keine starken Schatten
- **Kein Blitz**: Vermeiden, da es Reflexionen erzeugt
- **Indirekte Beleuchtung**: Falls künstliches Licht, dann diffus

#### ✅ Kamera-Einstellungen
- **Fokus**: Sicherstellen, dass der Text scharf ist
- **Abstand**: 20-30 cm vom Buch entfernt
- **Winkel**: Möglichst senkrecht zum Buch (90°)
- **Auflösung**: Minimum 1920x1080, besser höher

#### ✅ Buchpositionierung
- **Flache Oberfläche**: Buch auf einem Tisch platzieren
- **Kontrast**: Heller Hintergrund für dunkle Bücher, vice versa
- **Gerade Ausrichtung**: Buch parallel zur Kamera
- **Vollständig im Bild**: Alle Ränder sichtbar

#### ❌ Zu vermeiden
- **Unscharfe Bilder**: Verwacklungen vermeiden
- **Reflexionen**: Glänzende Oberflächen, Glasabdeckungen
- **Starke Schatten**: Ungleichmäßige Beleuchtung
- **Zu dunkle/helle Bilder**: Über- oder Unterbelichtung
- **Schräge Winkel**: Verzerrte Perspektiven
- **Teilweise verdeckt**: Finger im Bild, abgeschnittene Bereiche

## 📁 Dateistruktur und Benennungs-Modi

### 🎯 Flexible Bild-Upload-Optionen

Das Script unterstützt **zwei Modi** für Bild-Uploads:

#### **Option 1: Automatisch (Einfach)**
Lade einfach mehrere Bilder eines Buchs hoch - keine Labels erforderlich:

```
test_books/
├── modernesBuch.jpg          # Erstes Bild
├── modernesBuch_2.jpg        # Zweites Bild
├── modernesBuch_3.jpg        # Drittes Bild
├── altesBuch.jpg             # Ein anderes Buch
└── altesBuch_foto2.jpg       # Zweites Bild vom anderen Buch
```

**Vorteile:**
- ✅ Schnell und unkompliziert
- ✅ Keine spezielle Benennung nötig
- ✅ Ideal für Anfänger
- ✅ Automatische Gruppierung nach Buchname

#### **Option 2: Mit Labels (Empfohlen)**
Gib an, was jedes Bild zeigt für optimale Ergebnisse:

```
test_books/
├── modernesBuch_cover.jpg    # Cover (Vorderseite)
├── modernesBuch_spine.jpg    # Buchrücken
├── modernesBuch_back.jpg     # Rückseite mit ISBN
├── altesBuch_cover.jpg       # Cover eines anderen Buchs
└── altesBuch_isbn.jpg        # ISBN-Nahaufnahme
```

**Vorteile:**
- ✅ **Intelligente Priorisierung**: ISBN/Back-Bilder werden priorisiert
- ✅ **Bessere Reports**: Nachvollziehbare Ergebnisse
- ✅ **Gezielte Fehleranalyse**: Probleme schneller identifizieren

### Datei-Namenskonventionen

#### Format ohne Label (Automatisch)
```
{buchname}.{extension}
{buchname}_{nummer}.{extension}
{buchname}_{beliebiger_text}.{extension}
```

#### Format mit Label (Empfohlen)
```
{buchname}_{label}.{extension}
```

**Verfügbare Labels:**
- **`cover`** - Vorderseite/Cover (Titel, Autor, Artwork)
- **`spine`** - Buchrücken (manchmal Titel, Autor, Verlag)
- **`back`** - Rückseite (meist ISBN-Barcode)
- **`isbn`** - ISBN-Nahaufnahme
- **`pages`** - Innenseiten (Impressum mit Verlagsdaten)
- **`inside`** - Andere Innenbereiche

**Beispiele:**
- ✅ `harrypotter_cover.jpg` - Mit Label
- ✅ `harrypotter_back.jpg` - Mit Label
- ✅ `gatsby.jpg` - Ohne Label
- ✅ `gatsby_2.jpg` - Ohne Label
- ✅ `fachbuch_isbn.jpg` - Mit Label
- ❌ `IMG_1234.jpg` - Kein Buchname erkennbar

### Mischen erlaubt!

Du kannst beide Optionen kombinieren:

```
test_books/
├── buch1_cover.jpg     # Mit Label
├── buch1_back.jpg      # Mit Label
├── buch1_extra.jpg     # Ohne Label
├── buch2.jpg           # Ohne Label
└── buch2_2.jpg         # Ohne Label
```

**Hinweis:** Das Script gruppiert automatisch nach dem ersten Teil des Dateinamens (vor dem ersten Underscore).

## 🚀 Test-Script Ausführung

### Vorbereitung

1. **Verzeichnis erstellen:**
   ```bash
   mkdir test_books
   ```

2. **Fotos hinzufügen:**
   - Kopiere deine Buchfotos in das `test_books/` Verzeichnis
   - Benenne sie nach der oben beschriebenen Konvention

3. **Umgebungsvariablen setzen:**
   ```bash
   # Windows (PowerShell)
   $env:GEMINI_API_KEY="your-key-here"
   
   # Linux/Mac
   export GEMINI_API_KEY="your-key-here"
   ```

### Script ausführen

```bash
python test_real_world_books.py
```

Das Script fragt beim Start nach dem gewünschten Modus:

```
════════════════════════════════════════════════════════════════════════════════
Modus wählen:
  [1] Automatisch (empfohlen)
  [2] Interaktiv (Labels manuell setzen)
Wahl (1/2):
```

#### Modus 1: Automatisch (Standard)
- Labels aus Dateinamen werden automatisch erkannt
- Priorisierung erfolgt automatisch
- Keine weitere Interaktion erforderlich
- **Empfohlen** für die meisten Anwendungsfälle

#### Modus 2: Interaktiv
- Du kannst Labels nachträglich hinzufügen oder ändern
- Nützlich wenn Dateien nicht gelabelt sind
- Oder wenn du Labels anpassen möchtest

## 📊 Metriken und Performance

### Wichtige KPIs

1. **Erfolgsrate**: Sollte > 95% sein
2. **Durchschnittliche Dauer**: Target < 8s pro Buch

### Performance-Optimierung

Wenn die Performance nicht zufriedenstellend ist:

1. **Lange Verarbeitungszeit** (> 10s):
   - Internet-Verbindung prüfen (API-Calls)

2. **Niedrige Erfolgsrate** (< 90%):
   - Bildqualität verbessern
   - Mehr Bilder pro Buch (Cover + Spine)
   - API-Keys korrekt gesetzt?

## 🔧 Fehlerbehebung

### Häufige Probleme

#### Problem: "Bild-Verzeichnis nicht gefunden"
```
❌ Bild-Verzeichnis nicht gefunden: test_books
```

**Lösung:**
```bash
mkdir test_books
# Dann Bilder hinzufügen
```

#### Problem: "GEMINI_API_KEY nicht gesetzt"
```
⚠️  GEMINI_API_KEY nicht gesetzt
```

**Lösung:**
```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY="your-gemini-api-key"

# Linux/Mac
export GEMINI_API_KEY="your-gemini-api-key"
```

#### Problem: ISBN nicht gefunden
```
📖 ISBN: Nicht gefunden
```

**Lösungen:**
1. Rückseite des Buches fotografieren (da ist meist die ISBN)
2. Buchrücken fotografieren (manchmal auch ISBN)
3. Innenseite (Impressum) fotografieren
4. ISBN manuell im Bild positionieren (kein Schatten)

## 📋 Checkliste für erfolgreiche Tests

### Vor dem Test
- [ ] `test_books/` Verzeichnis erstellt
- [ ] Mindestens 1 Buch fotografiert (2-3 Bilder pro Buch)
- [ ] Dateien korrekt benannt (`buchname_bereich.jpg`)
- [ ] Umgebungsvariablen gesetzt (`GEMINI_API_KEY`)
- [ ] Dependencies installiert (`pip install -r requirements.txt`)

### Während des Tests
- [ ] Script startet ohne Fehler
- [ ] Alle Voraussetzungen erfüllt (grüne Häkchen)
- [ ] Bilder werden erkannt und verarbeitet
- [ ] Keine kritischen Fehler in der Konsole

### Nach dem Test
- [ ] JSON-Report generiert
- [ ] Erfolgsrate ≥ 90%
- [ ] ISBNs korrekt erkannt
- [ ] Titel und Autoren korrekt

## 💡 Tipps für beste Ergebnisse

### Allgemein
1. **Multiple Bilder**: 2-3 Bilder pro Buch erhöhen die Erkennungsrate
2. **ISBN-Fokus**: Mindestens ein Bild mit ISBN-Barcode
3. **Gute Beleuchtung**: Tageslicht oder gut ausgeleuchtete Räume
4. **API-Keys setzen**: Alle verfügbaren APIs nutzen
5. **Realistische Erwartungen**: Nicht jedes Buch wird perfekt erkannt

### Mit Labels
1. **Label `isbn` verwenden**: Für Nahaufnahmen der ISBN
2. **Label `back` verwenden**: Für Rückseite mit Barcode
3. **Konsistente Benennung**: Immer Kleinbuchstaben für Labels
4. **Automatischer Modus**: Spart Zeit bei vielen Büchern

## 🔗 Weiterführende Ressourcen

- [Test Books README](../../test_books/README.md) - Detaillierte Beispiele für beide Modi
- [Search Grounding](../../HANDOVER_2025-11-04_PART3_SEARCH_GROUNDING.md)

## 📞 Support

Bei Problemen:
1. Prüfe die Fehlerbehebung oben
2. Schaue in die Logs (`logs/` Verzeichnis)
3. Prüfe den JSON-Report für Details
4. Validiere die Bildqualität

---

**Letzte Aktualisierung:** 2026-02-05
**Version:** 2.1 - Bereinigt um OCR-Referenzen