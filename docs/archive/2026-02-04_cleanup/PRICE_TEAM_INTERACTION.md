# Preisagententeam: Interaktion & Architektur V2

Dieses Dokument beschreibt die optimierte Architektur (Stand: Januar 2026) für das Zusammenspiel zwischen dem **Strategist Agent** und den Research-Komponenten.

## 1. Übersicht & Rollen

Das System verzichtet auf den veralteten "Scout Agent" und setzt auf eine direkte Integration der Recherche-Logik in den Strategisten für maximale Effizienz, während ein separater Worker für Hintergrund-Aktualisierungen bereitsteht.

| Komponente | Typ | Verantwortung | Trigger |
| :--- | :--- | :--- | :--- |
| **Price Research Orchestrator** | `Shared Library` | Enthält die Kernlogik: Cache-Check, Gemini Search Grounding, Daten-Fusion und Speichern in Firestore. Wird von beiden Agenten genutzt. | *Code Call* |
| **Strategist Agent** | `Cloud Function` | **Der Entscheider.** Koordiniert den Ingestion-Prozess für ein neues Buch. Ruft den Orchestrator *direkt* auf, um Live-Preise zu erhalten. | Pub/Sub: `condition-assessment-completed` |
| **Price Research Agent** | `Cloud Function` | **Der Hintergrund-Arbeiter.** Führt regelmäßige Updates oder manuelle Re-Scans durch, ohne den Listing-Prozess direkt zu triggern. | Pub/Sub: `price-research-requests` |

## 2. Architektur-Diagramm

```mermaid
graph TD
    subgraph "Ingestion Flow (Fast Path)"
        A[Ingestion/Condition] -->|Pub/Sub| B(Strategist Agent)
        B -->|Direct Call| C{PriceResearchOrchestrator}
        C -->|Check| D[(Firestore Cache)]
        C -->|If Miss| E[Gemini Search Grounding]
        C -->|Save| D
        B -->|Calc Price| F[Final Price Decision]
        F -->|Update| G[(Firestore Book)]
        F -->|Pub/Sub| H[Listing Agent]
    end

    subgraph "Background Refresh (Slow Path)"
        I[Cloud Scheduler / UI] -->|Pub/Sub| J(Price Research Agent)
        J -->|Direct Call| C
        J -.->|Update Only| D
    end

    style B fill:#e1f5fe,stroke:#01579b
    style J fill:#f3e5f5,stroke:#4a148c
    style C fill:#fff9c4,stroke:#fbc02d
```

## 3. Detaillierter Datenfluss

### A. Der Standard-Prozess (Neues Buch)
Wenn ein Buch neu ins System kommt, muss der Preis **sofort** verfügbar sein, um den Listing-Prozess nicht zu blockieren.

1.  **Trigger:** Der `Strategist Agent` erhält die Nachricht, dass der Zustand bewertet wurde.
2.  **Orchestration:** Der Strategist instanziiert den `PriceResearchOrchestrator`.
3.  **Research (async):** Der Strategist ruft `await orchestrator.research_price(...)` auf.
    *   Der Orchestrator prüft `market_data` (Cache < 7 Tage).
    *   Bei Cache-Miss: Parallele Abfrage via Gemini Grounding (Dauer: ~5-10s).
    *   Ergebnisse werden in Firestore gespeichert.
4.  **Pricing:** Der Strategist lädt die **detaillierten Zustandsdaten** (AI Grade, Defect List) aus dem `condition_assessments`-Dokument. Diese werden zusammen mit den Marktdaten in den Prompt für die Preisfindung (LLM) injiziert. Dies ist entscheidend, da z.B. ein "Poor"-Zustand den Preis drastisch senkt, selbst wenn der Marktdurchschnitt hoch ist.
5.  **Completion:** Der Strategist setzt den Status auf `priced` und sendet das Buch an den Listing Agent.

### B. Der Background-Prozess (Refresh)
Preise veralten. Der `Price Research Agent` kümmert sich um Updates, ohne den komplexen Strategist-Flow (Zustandsbewertung, etc.) neu zu starten.

1.  **Trigger:** Cron-Job (z.B. "Älter als 30 Tage") oder Button im Dashboard sendet Nachricht an `price-research-requests`.
2.  **Execution:** Der `Price Research Agent` nutzt *denselben* `PriceResearchOrchestrator` Code.
3.  **Result:** Aktualisierte Daten landen in `market_data`. Das Buch-Dokument selbst wird *nicht* automatisch neu bepreist (dies kann optional durch einen weiteren Trigger erfolgen, falls gewünscht).

## 4. Technische Implementierung

### LLM Konfiguration
Für die Preisfindung im **Strategist Agent** wird explizit **Gemini 2.5 Pro** verwendet.
Dies gewährleistet eine höhere Reasoning-Qualität bei der Synthese von Marktdaten und Zustandsanalyse im Vergleich zu kleineren Modellen.

### Shared Library (`shared/price_research/orchestrator.py`)
Dies ist das Herzstück. Es entkoppelt die Logik von der Ausführungsumgebung.

```python
class PriceResearchOrchestrator:
    async def research_price(self, isbn, ...) -> Dict:
        # 1. Check Firestore Cache
        # 2. Call Gemini Grounding (if needed)
        # 3. Analyze & Fuse Data
        # 4. Save to Firestore
        return price_data
```

### Strategist Integration
Der Strategist wartet nicht auf Events, sondern auf den *Completion* des asynchronen Calls.

```python
# agents/strategist-agent/main.py
async def handle_event(cloud_event):
    # ... setup ...
    orchestrator = PriceResearchOrchestrator(db, grounding_client)
    
    # 1. Direct dependency - no external polling needed!
    market_data = await orchestrator.research_price(isbn, title, ...)
    
    # 2. Fetch Detailed Condition Data
    # WICHTIG: Wir nutzen nicht nur "book.condition", sondern die AI-Analyse!
    condition_doc = await db.collection('users').document(uid) \
                      .collection('condition_assessments').document(book_id).get()
    condition_details = condition_doc.to_dict() if condition_doc.exists else {}
    
    # 3. Inject into LLM Pricing Prompt
    # WICHTIG: Neben den Zustandsdaten müssen auch die Buch-Stammdaten explizit übergeben werden.
    # Das LLM benötigt Titel, Autor, Jahr etc. um die Marktdaten korrekt zu kontextualisieren.
    final_price = await calculate_price_with_llm(
        model="gemini-2.5-pro", # <-- Explicit Model Request
        market_data=market_data,
        condition_data=condition_details,
        book_metadata={
            "title": book_dict.get("title"),
            "author": book_dict.get("author"),
            "year": book_dict.get("year"),
            "isbn": book_dict.get("isbn"),
            "publisher": book_dict.get("publisher")
        } # <-- Explicit Metadata Injection
    )
    # ...
```

## 5. Frontend & Data Storage Integration

Um Transparenz ("White Box Pricing") zu gewährleisten, müssen Begründung und Quellen strukturiert gespeichert und im Frontend angezeigt werden.

### A. Firestore Schema (`books/{book_id}`)
Das Buch-Dokument wird um ein explizites `pricing` Objekt erweitert, das die Entscheidungsgrundlage speichert.

```json
{
  "calculatedPrice": 12.50,
  "pricing": {
    "generated_at": "2026-01-13T10:00:00Z",
    "method": "llm_v2_market_analysis",
    "reasoning": "Preis leicht unter Marktdurchschnitt (14€) angesetzt, da Schutzumschlag fehlt. Konkurrenzangebote bei Medimops ab 11.50€ (Poor condition).",
    "confidence_score": 0.85,
    "sources": [
      {
        "seller": "eBay",
        "price": 12.00,
        "currency": "EUR",
        "condition": "Good",
        "url": "https://ebay.com/itm/...",
        "relevance": "high"
      },
      {
        "seller": "Medimops",
        "price": 14.50,
        "currency": "EUR",
        "condition": "Very Good",
        "url": "https://medimops.de/...",
        "relevance": "medium"
      }
    ]
  }
}
```

### B. Frontend Anforderungen
Die Detailansicht im Dashboard (`BookList.jsx` / `BookDetail`) muss aktualisiert werden:

1.  **Reasoning Box:** Ein neuer UI-Block "Preisanalyse", der `pricing.reasoning` prominent anzeigt. Der Nutzer muss verstehen, *warum* der Preis gewählt wurde (z.B. Abschlag wegen Zustand).
2.  **Quellen-Liste:** Die bestehende Link-Liste wird auf `pricing.sources` umgestellt. Anzeige von Händler, Preis, Zustand und direktem Link.
3.  **Transparenz:** Falls `pricing.method` auf "fallback" steht (z.B. keine Marktdaten gefunden), muss dies dem Nutzer als Warnung angezeigt werden.

## 6. Migration & Cleanup Status

*   **Scout Agent:** Veraltet und entfernt.
*   **Price Research Agent:** Läuft als Hintergrund-Service.
*   **Strategist Agent:** Nutzt Library Call.

### Abgrenzung zum alten Design

*   **Kein Scout Agent mehr:** Die unzuverlässige Scraping-Schnittstelle wurde entfernt.
*   **Kein Polling:** Der Strategist muss nicht mehr `sleep()` und Firestore pollen, bis ein externer Agent fertig ist.
*   **Klare Trennung:**
    *   Strategist = Prozess-Owner für das **Buch**.
    *   Price Research Agent = Worker für **Marktdaten-Updates**.
