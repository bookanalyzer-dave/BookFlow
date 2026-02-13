# Strategist Agent (Pricing Agent) 🧠

**Aktualisiert:** 04.02.2026
**Status:** Aktiv / Implementation Gemini 2.0 Flash/Pro

Der **Strategist Agent** fungiert als zentrale "Pricing Engine" des Systems. Er wurde im Januar 2026 grundlegend überarbeitet (siehe [Pricing Simplification Report](../archive/PRICING_SIMPLIFICATION_REPORT_2026-01-20.md)), um komplexe State-Machines durch einen einzelnen, hochintelligenten "Super Request" an **Gemini 2.0 Flash / Pro** zu ersetzen.

## 1. Kern-Konzept: "Super Request"

Statt den Preisfindungsprozess in viele kleine Schritte (Recherche, Analyse, Berechnung) zu unterteilen, übergibt der Agent alle verfügbaren Kontextdaten in einem einzigen Prompt an das LLM.

### Eingabedaten (Multimodal Context)
1.  **Buch-Metadaten:** Titel, Autor, ISBN, Jahr, Verlag.
2.  **Condition Assessment:** JSON-Daten vom Condition Assessor (Grade, Scores, Defekte).
3.  **Visuelle Daten:** Alle Buch-Bilder (Cover, Spine, Pages) als Image-URLs.

### Tool Use: Google Search
Der Agent ist mit dem **Google Search Tool** ausgestattet (`googleSearchRetrieval`).
*   **Zweck:** Live-Recherche aktueller Marktpreise (Sold Listings, Active Listings).
*   **Vorteil:** Das Modell entscheidet selbstständig, welche Suchbegriffe notwendig sind, um den Preis zu verifizieren.

## 2. Workflow Integration

### Trigger
*   **Event:** Pub/Sub Topic `condition-assessment-completed`.
*   **Voraussetzung:** Condition Assessment muss abgeschlossen sein (Daten in Firestore).

### Prozess-Schritte
1.  **Initialization:** Agent empfängt Pub/Sub Message mit `bookId` und `uid`.
2.  **Data Gathering:** Lädt Buchdaten und Condition Assessment aus Firestore.
3.  **LLM Execution:**
    *   Konstruiert Prompt ("Expert antiquarian bookseller").
    *   Fügt Bilder und JSON-Daten hinzu.
    *   Ruft Gemini mit Search-Tool auf.
4.  **Parsing:** Extrahiert strukturiertes JSON aus der LLM-Antwort (`price`, `confidence`, `reasoning`).
5.  **Persistenz:** Speichert das Ergebnis in `users/{uid}/books/{bookId}` (Status: `priced`).
6.  **Next Step:** Sendet Nachricht an `book-listing-requests` (Ambassador Agent).

## 3. Technische Konfiguration

**Datei:** [`agents/strategist-agent/main.py`](../../agents/strategist-agent/main.py)

| Parameter | Wert | Beschreibung |
| :--- | :--- | :--- |
| **Model** | `gemini-2.0-flash` / `gemini-1.5-pro` | State-of-the-Art Modelle für Reasoning & Vision |
| **Temperature** | `0.1` | Minimiert Halluzinationen, maximiert Konsistenz |
| **Tools** | `googleSearchRetrieval` | Ermöglicht Zugriff auf Live-Web-Daten |
| **Output** | `JSON` | Strukturiertes Format für Backend-Verarbeitung |

## 4. Prompting Strategie

Der System-Prompt definiert die Persona eines "Expert Antiquarian Bookseller". Er erzwingt:
1.  Visuelle Analyse der Bilder.
2.  Berücksichtigung des Condition Reports.
3.  **Verpflichtende** Nutzung der Google Suche zur Preisvalidierung.
4.  Ausgabe eines JSON-Objekts.

## 5. Vorteile der neuen Architektur

*   **Geschwindigkeit:** Nur ein LLM-Call statt mehrerer Agent-Roundtrips.
*   **Kontext-Verständnis:** Das Modell "sieht" den Zustand (Bilder) und "kennt" den Marktpreis gleichzeitig.
*   **Wartbarkeit:** Kein komplexer Code für Fallback-Algorithmen oder Web-Scraper (Scout Agent) mehr nötig.
*   **Robustheit:** Nutzung des System-Level LLM für Quota-Handling und Billing.

## 6. Known Issues / Limitations

*   **Quota:** Gemini Pro Modelle können striktere Rate Limits haben als Flash-Modelle.
*   **Search Latency:** Die Nutzung des Search Tools kann die Response-Time auf 10-20 Sekunden erhöhen.

---
**Historie:**
*   *V1 (2025):* Multi-Agent System mit Scout Agent und komplexer Formel-Logik.
*   *V2 (Jan 2026):* Simplification auf Gemini Pro "Super Request".
*   *V3 (Feb 2026):* Refactoring auf System-Level API Key.
