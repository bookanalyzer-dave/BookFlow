# Session Handover - 09.02.2026

## Status: STABIL & LIVE 🟢

### Architektur-Update
Die Pipeline wurde repariert und erweitert:
1.  **Ingestion Agent:** Identifiziert Buch (Gemini 2.5 Pro).
    - *Neu:* Extrahiert jetzt auch **Gewicht** (`weight_grams`) und **Einband** (`binding_type`).
    - *Fix:* Sendet korrekt an Pub/Sub Topics `condition-assessment-jobs` UND `price-research-requests`.
2.  **Condition Assessor:** Bewertet Zustand (Gemini 2.5 Flash).
    - *Trigger:* `condition-assessment-jobs`.
3.  **Strategist Agent:** Berechnet Preis.
    - *Trigger:* `condition-assessment-completed`.
    - *Input:* Metadaten + Zustandsbericht.

### Frontend (Dashboard)
- URL: `https://project-52b2fab8-15a1-4b66-9f3.web.app`
- Tech: React + Tailwind + Firebase Hosting.
- *Neu:* Zeigt Gewicht, Einband, ISBN, Verlag sauber an.
- *Neu:* Klickbare Quellen-Links bei der Preisanalyse.

### Deployment Tricks
- **Backend:** `gcloud builds submit --config ops/cloudbuild/cloudbuild.ingestion-agent.yaml .`
- **Frontend:** Am besten lokal im Container via `npx firebase-tools deploy` (mit Service Account Key), da Cloud Build manchmal IAM-Probleme mit Firebase hat.
- **Service Account Key:** Liegt unter `/home/mettnerd777/.openclaw/workspace/gcp-key.json`.

### Nächste Schritte
- Ebay-Listing Integration testen.
- Bulk-Upload Performance prüfen.

-- Harald der Hacker
