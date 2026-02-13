# Projektstruktur
Datum: 2026-02-04 (Aktualisiert)

Dies ist die aktuelle Verzeichnisstruktur des Projekts "Intelligent Book Sales Pipeline" (IBSP). Diese Struktur wurde optimiert, um Skalierbarkeit, Wartbarkeit und eine klare Trennung der Verantwortlichkeiten zu gewährleisten.

## Root Directory (`/`)

Das Hauptverzeichnis enthält Konfigurationsdateien für die Infrastruktur, Build-Prozesse und Entwicklungstools.

*   `cloudbuild.yaml` / `cloudbuild.*.yaml`: Google Cloud Build Konfigurationen für CI/CD Pipelines.
*   `firebase.json`: Konfiguration für Firebase Hosting, Rules und Emulatoren.
*   `firestore.rules`: Security Rules für Cloud Firestore.
*   `requirements.txt`: Globale Python-Abhängigkeiten (Development).
*   `setup.py`: Setup-Skript für das `shared` Package.
*   `README.md`: Einstiegspunkt für neue Entwickler.

## Agents (`agents/`)

Hier befinden sich die Microservices (Cloud Run Functions / Services), die die Kernlogik der Pipeline bilden. Jeder Agent hat sein eigenes Verzeichnis mit `main.py` (Entrypoint), `Dockerfile` und `requirements.txt`.

*   `ingestion-agent/`:
    *   Verantwortlich für Bildanalyse und Metadaten-Extraktion via Gemini.
    *   Nutzt `shared.simplified_ingestion` für die Business-Logik.
    *   Trigger: Pub/Sub (`trigger-ingestion`).
    *   Nutzt Dead Letter Queue (`trigger-ingestion-dlq`).
*   `condition-assessor/`:
    *   Verantwortlich für die Zustandsbewertung von Büchern.
    *   Trigger: Firestore (`condition_assessment_requests`).
*   `strategist-agent/`:
    *   Verantwortlich für Preisstrategie und Listing-Entscheidungen.
*   `scout-agent/`:
    *   **(Deprecated)** Ehemals Web-Scraping, jetzt durch Google Search Tool im Strategist Agent ersetzt.
*   `sentinel-agent/`:
    *   Überwacht Verkäufe und triggert Delistings.
*   `sentinel-webhook/`:
    *   Empfängt Webhooks von externen Plattformen (z.B. eBay).
*   `ambassador-agent/`:
    *   Handhabt API-Integrationen mit Verkaufsplattformen (Listing/Delisting).

## Dashboard (`dashboard/`)

Die Benutzeroberfläche für Nutzer und Administratoren.

*   `frontend/`:
    *   React-Anwendung (Vite).
    *   Komponenten für Upload, Buchliste, Detailansicht.
    *   Firebase Hosting.
*   `backend/`:
    *   Python Flask API (Cloud Run).
    *   Handhabt Upload-Signierung, Auth-Verifizierung und Ingestion-Trigger.

## Shared Library (`shared/`)

Gemeinsam genutzter Code, der als internes Python-Package installiert wird. Dies verhindert Code-Duplizierung zwischen Agents.

*   `apis/`: Clients für externe APIs (Google Books, OpenLibrary, Data Fusion).
*   `firestore/`: Typisierte Clients und Modelle für Firestore-Zugriffe.
*   `simplified_ingestion/`:
    *   Kernlogik der neuen Ingestion-Pipeline.
    *   `core.py`: Orchestrierung.
    *   `models.py`: Pydantic Modelle.
*   `user_llm_manager/`:
    *   **(Legacy / Scheduled for removal)** Alte Abstraktionsschicht für LLM-Provider. Wird durch direkte Gemini-Integration ersetzt.
*   `monitoring/`: Metrics und Logging Utilities.
*   `image_sorter/`: Klassifizierung von Buchbildern (Cover, Spine, etc.).

## Documentation (`docs/`)

Die Projektdokumentation ist in drei Bereiche unterteilt:

*   `current/`: **Die aktuelle, gültige Dokumentation.** Hier sollte man zuerst suchen.
    *   `TECHNICAL_ARCHITECTURE.md`: High-Level Architektur.
    *   `PROJECT_STRUCTURE.md`: Diese Datei.
    *   `CONFIGURATION_REFERENCE.md`: Überblick über Environment Variables und Konfiguration.
*   `archive/`: Veraltete Dokumente (inkl. alter OCR-Doku), Logs und Pläne. Dienen nur der historischen Referenz.
*   `deployment/`: Anleitungen und Checklisten für Deployments.
*   `debugging/`: Hilfen zur Fehlerbehebung (z.B. `UPLOAD_ERROR_GUIDE.md`).
*   `testing/`: Test-Reports und Anleitungen.
*   `operations/`: Runbooks für den Betrieb (Backups, Monitoring).

## Logs (`logs/`)

*   Enthält lokale Log-Dateien von Testläufen und Skripten.
*   `archive/`: Archivierte Logs.
*   In Production werden Logs direkt an Cloud Logging gesendet.

## Tests (`tests/`)

*   Integrationstests und Unit-Tests.
*   `manual_scripts/`: Skripte für manuelle E2E-Tests.

## Ops & Scripts (`ops/`, `scripts/`)

*   `ops/monitoring/`: Skripte für Monitoring-Setup (Cloud Monitoring Dashboards).
*   `scripts/`: Utility-Skripte für Entwicklung und Maintenance (z.B. Datenbank-Migrationen).
