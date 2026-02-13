# Test Books Directory

Dieses Verzeichnis ist für Real-World Testing mit echten Buchfotos.

## ⚠️ NEUE SYSTEM-LIMITS

**Das System unterstützt jetzt:**
- ✅ **1 Buch pro Upload** (nicht mehr 4)
- ✅ **Maximal 10 Bilder** pro Buch (nicht mehr 20)

Diese Limits gelten insbesondere für den Image Sorter Agent (Modus 3).

## 📸 Dateibenennungs-Optionen

### Option 1: Automatisch (Einfach)

Lade einfach alle Fotos eines Buchs hoch - keine Labels erforderlich:

```
test_books/
├── modernesBuch.jpg
├── modernesBuch_2.jpg
├── modernesBuch_3.jpg
├── altesBuch.jpg
└── altesBuch_foto2.jpg
```

**Vorteile:**
- ✅ Schnell und unkompliziert
- ✅ Keine spezielle Benennung nötig
- ✅ Für Anfänger ideal

**So funktioniert's:**
- Das Script gruppiert automatisch nach dem ersten Teil des Dateinamens
- `modernesBuch.jpg`, `modernesBuch_2.jpg` → 1 Buch namens "modernesBuch"
- Bilder werden in der Reihenfolge verarbeitet, wie sie gefunden werden

### Option 2: Mit Labels (Empfohlen)

Gib an, was jedes Bild zeigt für bessere Ergebnisse:

```
test_books/
├── modernesBuch_cover.jpg      # Vorderseite
├── modernesBuch_spine.jpg      # Buchrücken
├── modernesBuch_back.jpg       # Rückseite (oft mit ISBN)
├── altesBuch_cover.jpg
└── altesBuch_pages.jpg         # Innenseiten
```

**Vorteile:**
- ✅ Intelligente Priorisierung von ISBN/Back-Bildern
- ✅ Bessere Nachvollziehbarkeit in Reports
- ✅ Gezieltere Fehleranalyse
- ✅ Optimale Verarbeitungsreihenfolge

### Verfügbare Labels

- **`cover`** - Vorderseite/Cover (Titel, Autor, Cover-Artwork)
- **`spine`** - Buchrücken (manchmal Titel, Autor, Verlag)
- **`back`** - Rückseite (oft ISBN-Barcode hier)
- **`isbn`** - Nahaufnahme der ISBN
- **`pages`** - Innenseiten (Impressum mit Verlagsdaten)
- **`inside`** - Andere Innenbereiche

### Label-Priorisierung

Das Script verarbeitet Bilder in folgender Reihenfolge:

1. **`isbn`** - Höchste Priorität (oft schnellste ISBN-Erkennung)
2. **`back`** - Zweithöchste Priorität (meist ISBN-Barcode)
3. **`cover`** - Dritthöchste Priorität (Titel und Autor)
4. **`spine`** - Vierthöchste Priorität (manchmal Titel)
5. **Ungelabeled** - Niedrigste Priorität

### Mischen erlaubt!

Du kannst beide Optionen kombinieren (aber max. 10 Bilder):

```
test_books/
├── meinbuch_cover.jpg   # Mit Label (wird priorisiert)
├── meinbuch_back.jpg    # Mit Label (wird priorisiert)
├── meinbuch_spine.jpg   # Mit Label
├── meinbuch_pages.jpg   # Mit Label
└── meinbuch_extra.jpg   # Ohne Label (wird später verarbeitet)
```

**Wichtig:** Bei mehr als 10 Bildern werden nur die ersten 10 verwendet!

## 🚀 Modi

### Modus 1: Automatisch (Standard)

```bash
python test_real_world_books.py
# Wähle [1] Automatisch
```

- Labels aus Dateinamen werden automatisch erkannt
- Keine weitere Interaktion erforderlich
- Empfohlen für die meisten Anwendungsfälle

### Modus 2: Interaktiv

```bash
python test_real_world_books.py
# Wähle [2] Interaktiv
```

- Du kannst Labels nachträglich hinzufügen oder ändern
- Nützlich wenn du vergessen hast, Dateien zu labeln
- Oder wenn du Labels anpassen möchtest

**Interaktiver Dialog:**
```
🏷️  INTERAKTIVER LABEL-MODUS
════════════════════════════════════════════════════════════════════════════════

Möchtest du Bilder kategorisieren für bessere Ergebnisse?
Verfügbare Labels: cover, spine, back, isbn, pages, inside
(Drücke Enter um Label zu überspringen)

📚 Buch: modernesBuch
   1. modernesBuch.jpg
      Label (cover/spine/back/isbn/pages/inside oder Enter): back
   2. modernesBuch_2.jpg
      Label (cover/spine/back/isbn/pages/inside oder Enter): cover
```

## 📁 Vollständiges Beispiel

```
test_books/
├── README.md                        # Diese Datei
│
├── harrypotter_cover.jpg           # Harry Potter - Cover
├── harrypotter_spine.jpg           # Harry Potter - Buchrücken
├── harrypotter_back.jpg            # Harry Potter - Rückseite mit ISBN
│
├── gatsby_cover.jpg                # Der große Gatsby - Cover
├── gatsby_back.jpg                 # Der große Gatsby - Rückseite
│
├── fachbuch.jpg                    # Ungelabeltes Fachbuch (Foto 1)
├── fachbuch_2.jpg                  # Ungelabeltes Fachbuch (Foto 2)
│
└── roman_isbn.jpg                  # Roman - Nahaufnahme ISBN
```

**Was passiert:**
1. **harrypotter**: 3 Bilder mit Labels → `back` wird zuerst verarbeitet
2. **gatsby**: 2 Bilder mit Labels → `back` wird zuerst verarbeitet
3. **fachbuch**: 2 Bilder ohne Labels → werden in Reihenfolge verarbeitet
4. **roman**: 1 Bild mit `isbn` Label → höchste Priorität bei Verarbeitung

## 🎯 Best Practices

### Für beste Ergebnisse

1. **2-10 Bilder pro Buch** (LIMIT: maximal 10)
   - Ein Bild mit ISBN (back/spine/isbn) - WICHTIG!
   - Ein Bild vom Cover
   - Optional: Weitere Details (Spine, Pages, etc.)
   - ⚠️ Mehr als 10 Bilder werden automatisch reduziert

2. **Klare Labels verwenden**
   - `buch_back.jpg` statt `buch_rueckseite.jpg`
   - Verwende die vordefinierten Labels

3. **Gute Bildqualität**
   - Scharfer Fokus
   - Gute Beleuchtung
   - Keine Reflexionen

4. **ISBN-Bereich**
   - Fotografiere immer die Rückseite (meist ISBN-Barcode)
   - Oder Buchrücken (manchmal auch ISBN)
   - Nahaufnahmen mit Label `isbn` für beste Erkennung

### Beispiel-Workflow

**Schnell (Option 1) - MAX 10 Bilder:**
```bash
# 1. Fotos machen (max 10!)
smartphone_foto1.jpg
smartphone_foto2.jpg
smartphone_foto3.jpg
# ... (max 10 Fotos)

# 2. Umbenennen
mv smartphone_foto1.jpg test_books/meinbuch.jpg
mv smartphone_foto2.jpg test_books/meinbuch_2.jpg
mv smartphone_foto3.jpg test_books/meinbuch_3.jpg

# 3. Script ausführen
python test_real_world_books.py
```

**Optimal (Option 2) - MAX 10 Bilder:**
```bash
# 1. Fotos gezielt machen und direkt benennen (max 10!)
test_books/meinbuch_cover.jpg   # Cover fotografiert
test_books/meinbuch_back.jpg    # Rückseite fotografiert (ISBN!)
test_books/meinbuch_spine.jpg   # Buchrücken fotografiert
test_books/meinbuch_isbn.jpg    # ISBN Nahaufnahme (optional)
# ... (max 10 Fotos insgesamt)

# 2. Script ausführen
python test_real_world_books.py
# → Labels werden automatisch erkannt und priorisiert
```

## ✅ Was du brauchst

### Minimum (Kritisch)
- ✅ Mindestens 1 Buchfoto in diesem Verzeichnis

### Optional (Empfohlen für beste Ergebnisse)
- ⚠️ `GEMINI_API_KEY` Umgebungsvariable gesetzt

## 📚 Weiterführende Dokumentation

- **Vollständiger Testing Guide:** [`docs/testing/REAL_WORLD_TESTING_GUIDE.md`](../docs/testing/REAL_WORLD_TESTING_GUIDE.md)

## 🎯 Quick Start

### Absolute Minimum (3 Schritte)
```bash
# 1. Foto machen und ins Verzeichnis kopieren
copy C:\Users\...\IMG_1234.jpg test_books\meinbuch.jpg

# 2. Script ausführen
python test_real_world_books.py

# 3. Modus wählen: [1] Automatisch oder [3] Image Sorter
```

### Empfohlen (5 Schritte) - MAX 10 Bilder!
```bash
# 1. Mehrere Fotos machen (Cover, Rückseite, etc.) - MAX 10!

# 2. Mit Labels benennen und kopieren
copy IMG_1234.jpg test_books\meinbuch_cover.jpg
copy IMG_1235.jpg test_books\meinbuch_back.jpg
copy IMG_1236.jpg test_books\meinbuch_isbn.jpg
# ... (max 10 Bilder insgesamt)

# 3. Script ausführen
python test_real_world_books.py

# 4. Modus wählen:
#    [1] Automatisch
#    [3] Image Sorter (AI-powered, 1 Buch, max 10 Bilder)

# 5. Report analysieren
```

### Image Sorter Modus (Neu)
```bash
# Modus [3] wählen für:
# - Automatische Klassifikation mit Gemini Flash
# - Nur 1 Buch, maximal 10 Bilder
# - GUI zur Review & Bearbeitung der Labels
# - Keine Buch-Zuordnung nötig (alles wird "Buch 1")
```

---

**Viel Erfolg beim Testen! 🚀**