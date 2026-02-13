# Startbefehle für die lokale Entwicklung

## Frontend

Führen Sie diesen Befehl im Verzeichnis `dashboard/frontend` aus:

```bash
npm run dev
```

## Backend

Führen Sie diesen Befehl im Verzeichnis `dashboard/backend` aus. Stellen Sie sicher, dass die virtuelle Umgebung (`venv`) aktiviert ist.

**PowerShell (Windows):**
```powershell
.\venv\Scripts\activate; $env:GOOGLE_APPLICATION_CREDENTIALS="D:\Neuer Ordner\service-account-key.json"; $env:FLASK_APP="main.py"; $env:GCP_PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"; $env:GCS_BUCKET_NAME="project-52b2fab8-15a1-4b66-9f3-book-images"; $env:PORT="5000"; flask run --port 5000
```

**Bash (Linux/macOS):**
```bash
source venv/bin/activate; export GOOGLE_APPLICATION_CREDENTIALS="<path_to>/service-account-key.json"; export FLASK_APP="main.py"; export GCP_PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"; export GCS_BUCKET_NAME="project-52b2fab8-15a1-4b66-9f3-book-images"; export PORT="5000"; flask run --port 5000
