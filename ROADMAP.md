# ROADMAP: BuchanalyseMCL (BookFlow)

## Status Quo: Was funktioniert im Code nachweislich?
- **Backend Setup & API:** Die Flask-App in `dashboard/backend/main.py` ist konfiguriert und routet ordnungsgemäß Endpunkte. Rate-Limiting und CORS (für die `.web.app`) sind aktiv. Der Live-CORS-Test auf die Cloud Run Instanz (`dashboard-backend-563616472394`) war erfolgreich.
- **Firebase Auth & Token Verification:** Auth-Überprüfung per Bearer Token.
- **GCP Services Integration:** 
  - **Cloud Storage:** Generierung von Signed URLs für den Upload.
  - **Pub/Sub:** Das Backend pusht Nachrichten auf Topics für asynchrone Verarbeitung (`ingestion-requests`, `trigger-condition-assessment`). Ein Environment-Repair-Script fängt fehlerhafte Quotes/Spaces ab.
  - **Firestore:** Bücher-Status wird via Shared-Library geschrieben.
- **Ingestion Agent:** In `agents/ingestion-agent/main.py` existiert ein Pub/Sub getriggerter Agent, der Bilder analysiert und nachfolgende Events feuert.

## Bugs/Leaks: Lücken zwischen Code-Logik und der Live-Experience
- **Umgebungsvariablen-Workaround (Der Haupt-Blocker):** Das `bootstrap_env()`-Skript im Backend repariert "dreckige" Umgebungsvariablen (Quotes, Leerzeichen, verdoppelte Projekt-IDs). **Die Cloud-Agenten (Condition Assessor, Price Research) haben diesen Hack nicht.** Sie crashen daher in der Cloud Umgebung, da sie mit fehlerhaften GCP_PROJECT oder GCS_BUCKET_NAME Werten arbeiten.
- **CORS / Frontend-Backend-Verbindung:** Das Frontend läuft unter `https://project-52b2fab8-15a1-4b66-9f3.web.app/` und ist in der CORS-Liste des Backends erlaubt. Login und Upload müssen noch in einem End-to-End Test in einem Browser (z.B. Playwright) final validiert werden, da der Sandbox-Browser-Test technisch limitiert war.

## Cloud-Migration: Infrastruktur-Sanierung
1. **Pipeline-Sanierung in Cloud Build:** Die `ops/cloudbuild/*.yaml` Dateien übergeben Umgebungsvariablen über einen langen, kommaseparierten String (`--set-env-vars=VAR1=...,VAR2=...`). Dies führt in Kombination mit Cloud Build Variablen-Substitution (`${PROJECT_ID}`) zu Parsing-Fehlern (Quotes/Leerzeichen). 
   - *Lösung:* Wechsle auf `--set-env-vars-file` oder formatiere die Flags in den gcloud-Commands strikt als einzelne Array-Elemente ohne Quotierungs-Konflikte.
2. **Entfernen des `bootstrap_env()`-Hacks:** Sobald die Cloud Build Skripte repariert sind, muss der Hack aus der `main.py` des Backends entfernt werden.
3. **Agenten-Deployment standardisieren:** Stelle sicher, dass alle Agenten (Ingestion, Condition, Price) mit identischen, sauberen Cloud Build Workflows deployt werden.
4. **Shared Library als Package:** Die Shared Library (aktuell hartcodiert referenziert) sollte sauber paketiert werden.