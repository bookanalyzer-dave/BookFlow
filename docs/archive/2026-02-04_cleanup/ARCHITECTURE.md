# Systemarchitektur

Dieses Dokument beschreibt die High-Level-Architektur des automatisierten Buchverkaufssystems. Das System ist als eine ereignisgesteuerte, serverlose Architektur auf der Google Cloud Platform (GCP) konzipiert und besteht aus einer Reihe von spezialisierten Microservices, den "Agenten".

## Kernprinzipien

-   **Serverless:** Alle Agenten sind als Cloud Functions implementiert, was eine automatische Skalierung und nutzungsbasierte Kosten ermöglicht.
-   **Ereignisgesteuert:** Die Agenten kommunizieren asynchron über Pub/Sub-Nachrichten und Firestore-Events. Dies entkoppelt die Dienste und erhöht die Resilienz.
-   **Spezialisierung:** Jeder Agent hat eine klar definierte Aufgabe, was die Wartbarkeit und Testbarkeit verbessert.
-   **KI-gestützt:** Das System nutzt intensiv Vertex AI (Gemini Pro), um komplexe Aufgaben wie die Bildanalyse und Texterstellung zu automatisieren.

## Architektur-Diagramm (Logisch)

```mermaid
graph TD
    subgraph User Interaction
        A[Benutzer] --> B{Dashboard Frontend};
        B --> C[Dashboard Backend API];
    end

    subgraph Data Flow & Processing
        C -->|1. Bilder-Upload| D[Cloud Storage];
        D -->|2. Trigger| E[Pub/Sub: book-analyzed];
        E -->|3. Start| F(Ingestion Agent);
        F -->|4a. Analyse| G[Vertex AI: Gemini];
        F -->|4b. Anreicherung| H[Google Books API];
        F -->|5. Speichern| I[Firestore: /books/{bookId}];
        
        I -->|6a. Status: ingested| J(Strategist Agent);
        J -->|7. Preis berechnen| I;
        J -->|8. Listing anstoßen| K[Pub/Sub: book-listing-requests];
        K -->|9. Listen| L(Ambassador Agent);
        L -->|10. Externe API| M[eBay API];
        L -->|11. Status-Update| I;

        I -->|6b. Status: needs_review| B;
        B -->|Korrektur| C;
        C -->|Reprocess| E;
    end

    subgraph Monitoring & Sales
        M -->|Verkauf| N[Sentinel Webhook];
        N -->|Benachrichtigung| O[Pub/Sub: sale-notification-received];
        O -->|Verarbeiten| P(Sentinel Agent);
        P -->|12. Status: sold| I;
        P -->|13. Delisting anstoßen| Q[Pub/Sub: delist-book-everywhere];
        Q -->|14. Delisten| L;
    end
    
    subgraph Market Data
        R[Cloud Scheduler] --> S(Scout Agent);
        S --> T[Externe Webseiten];
        S --> U[Firestore: /market_data];
    end
```

## Komponenten & Datenfluss

### 1. Erfassung & Analyse (`ingestion-agent`)
-   **Trigger:** Eine Pub/Sub-Nachricht auf Topic `book-analyzed` nach dem initialen Bild-Upload oder eine "Reprocess"-Anfrage vom Backend.
-   **Aufgabe:** Führt die "Intelligente Forschungs-Pipeline" aus. Nutzt den `UserLLMManager`, um das Buch anhand der Bilder zu identifizieren, die Daten über die Google Books API anzureichern, bei Bedarf eine Deep Research zur Editions-Bestimmung durchzuführen und eine hochwertige Produktbeschreibung zu generieren.
-   **Ergebnis:** Ein umfassendes Buchdokument in Firestore mit dem Status `ingested` (hohe Sicherheit) oder `needs_review` (niedrige Sicherheit für manuelle Prüfung).

### 2. Manuelle Überprüfung (Human-in-the-Loop)
-   **Trigger:** Ein Buch erhält den Status `needs_review`.
-   **Aufgabe:** Das Frontend zeigt diese Bücher in einer separaten Ansicht an. Ein Benutzer kann die Kerndaten (Titel, Autor, ISBN) korrigieren.
-   **Ergebnis:** Ein API-Aufruf an das Backend stößt den `ingestion-agent` erneut an, diesmal mit den vom Benutzer validierten Daten als Ausgangspunkt.

### 3. Preisstrategie (`strategist-agent` & `scout-agent`)
-   **Trigger:** Ein Buch erhält den Status `ingested`.
-   **Aufgabe:** Der `scout-agent` sammelt periodisch Preisdaten von Wettbewerbern und speichert sie in der `market_data`-Collection (mit einer 60-Tage-TTL-Policy zur automatischen Bereinigung). Der `strategist-agent` analysiert diese Daten, berechnet einen optimalen Preis und speichert ihn im Buchdokument.
-   **Ergebnis:** Das Buch ist vollständig für den Verkauf vorbereitet. Der `strategist-agent` sendet eine Nachricht an Pub/Sub, um den Listing-Prozess zu starten.

### 4. Listing (`ambassador-agent`)
-   **Trigger:** Eine Pub/Sub-Nachricht vom `strategist-agent`.
-   **Aufgabe:** Nutzt eine erweiterbare Architektur, um das Buch auf externen Plattformen wie eBay zu listen.
-   **Ergebnis:** Das Buch ist online zum Verkauf verfügbar. Der Listing-Status wird in Firestore vermerkt.

### 5. Verkaufsabwicklung (`sentinel`-System)
-   **Trigger:** Eine Verkaufsbenachrichtigung von einer externen Plattform (z.B. eBay-Webhook).
-   **Aufgabe:** Der `sentinel-webhook` empfängt die Benachrichtigung und leitet sie sicher an den `sentinel-agent` weiter. Dieser aktualisiert den Buchstatus in Firestore auf `sold` und beauftragt den `ambassador-agent`, das Buch von allen anderen Plattformen zu entfernen.
-   **Ergebnis:** Ein Doppelverkauf wird verhindert und der Buchstatus ist im gesamten System aktuell.

## Code-Qualität & Best Practices

### Environment Variables Validation
Alle Agenten implementieren eine `validate_environment()` Funktion, die beim Start überprüft:
- Ob alle kritischen Umgebungsvariablen gesetzt sind
- Frühzeitiges Fehlschlagen mit klaren Fehlermeldungen
- Logging der erfolgreichen Validierung

### Type Hints
Alle Agent-Funktionen nutzen Python Type Hints für:
- Verbesserte Code-Lesbarkeit
- Bessere IDE-Unterstützung
- Früherkennung von Typ-Fehlern
- Automatische Dokumentation

### Code-Organisation
- Ungenutzte Imports wurden entfernt
- Konsistente Logging-Konfiguration
- Klare Funktionssignaturen mit Rückgabetypen

### Entfernte Agenten
-   **`scribe-agent`:** Die Funktionalität zur Beschreibungserstellung wurde vollständig in den `ingestion-agent` integriert, um Redundanzen zu beseitigen und den Prozess zu optimieren.