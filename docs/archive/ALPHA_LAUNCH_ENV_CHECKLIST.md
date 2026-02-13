# Alpha Launch - Environment Configuration Checklist

## Status: 🟡 IN PROGRESS

Dieser Guide führt dich durch die komplette Environment-Konfiguration für den Alpha Launch.

---

## 📋 Übersicht: Environment-Dateien Status

### ✅ Vollständig konfiguriert
- `service-account-key.json` - GCP Service Account (bereits vorhanden)
- `true-campus-475614-p4-7ce543618d8d.json` - Alternative GCP Credentials (bereits vorhanden)

### ⚠️ Teilweise konfiguriert (erfordert Ergänzungen)
- `dashboard/backend/.env` - Backend Konfiguration (BASIS vorhanden, API Keys fehlen)
- `agents/ingestion-agent/.env.yaml` - Ingestion Agent (BASIS vorhanden)
- `agents/condition-assessor/.env.yaml` - Condition Assessor (BASIS vorhanden)

### ❌ Nicht vorhanden (Agents ohne .env Templates)
Die folgenden Agents haben KEINE `.env.example` Templates und benötigen daher keine separaten .env Dateien:
- `agents/scout-agent/` - Verwendet GCP Umgebungsvariablen
- `agents/strategist-agent/` - Verwendet GCP Umgebungsvariablen
- `agents/ambassador-agent/` - Verwendet GCP Umgebungsvariablen
- `agents/sentinel-agent/` - Verwendet GCP Umgebungsvariablen
- `agents/sentinel-webhook/` - Verwendet GCP Umgebungsvariablen

---

## 🔑 Erforderliche API Keys & Credentials

### 1. GCP / Firebase Konfiguration ✅ VORHANDEN

**Status:** ✅ Vollständig konfiguriert

**Dateien:**
- `service-account-key.json` ✅
- `true-campus-475614-p4-7ce543618d8d.json` ✅

**GCP Project ID:** `true-campus-475614-p4`

**Konfigurierte Services:**
- Firestore
- Cloud Storage Bucket: `intelligent-research-pipeline-bucket`
- Vertex AI Location: `europe-west1`
- Cloud Functions
- Cloud Run

**Was funktioniert:**
- Firebase Authentication
- Firestore Datenbank
- Cloud Storage für Buchbilder
- Service Account Authentifizierung

---

### 2. Google Books API Key ⚠️ OPTIONAL

**Status:** ⚠️ Optional für Alpha

**Wo benötigt:**
- `dashboard/backend/.env` → `GOOGLE_BOOKS_API_KEY`
- `agents/ingestion-agent/.env.yaml` → `GOOGLE_BOOKS_API_KEY`

**Zweck:**
- Erweiterte Buchsuche
- Höhere Rate Limits
- Mehr Metadaten

**Für Alpha:**
- ✅ NICHT ZWINGEND ERFORDERLICH
- System funktioniert auch ohne (mit reduzierten Rate Limits)
- Empfohlen für bessere Performance

**Wie erhalten:**
1. Gehe zu: https://console.cloud.google.com/apis/credentials
2. Wähle Projekt: `true-campus-475614-p4`
3. Erstelle API Key
4. Aktiviere "Books API"
5. Trage ein in `.env` Dateien

---

### 3. User LLM API Keys (Optional) ⚠️ OPTIONAL

**Status:** ⚠️ Optional - Für User-eigene LLM Nutzung

Diese Keys ermöglichen Usern, ihre eigenen LLM Accounts zu verwenden:

#### OpenAI API Key
- **Zweck:** User kann eigene OpenAI API verwenden
- **Konfiguration:** Über Dashboard UI (nicht .env)
- **Für Alpha:** Optional - System funktioniert mit Gemini

#### Google AI API Key (Gemini)
- **Zweck:** User kann eigenen Google AI Account verwenden
- **Konfiguration:** Über Dashboard UI (nicht .env)
- **Für Alpha:** Optional - System nutzt Projekt Gemini

#### Anthropic API Key (Claude)
- **Zweck:** User kann eigenen Claude Account verwenden
- **Konfiguration:** Über Dashboard UI (nicht .env)
- **Für Alpha:** Optional - System funktioniert mit Gemini

**Wichtig:** Diese Keys werden NICHT in .env Dateien gespeichert, sondern:
- Verschlüsselt in Firestore pro User
- Über Dashboard UI konfiguriert
- Vollständig optional für Alpha

---

### 4. eBay API Keys ❌ ERFORDERLICH (SPÄTER)

**Status:** ❌ Noch nicht konfiguriert

**Für Alpha Phase:**
- ✅ NICHT SOFORT BENÖTIGT
- Wird erst für Ambassador Agent (Listing) benötigt
- In Phase 2 der Alpha implementierung

**Wann benötigt:**
- Sobald Ambassador Agent aktiviert wird
- Für automatisches Listing auf eBay

**Was vorbereiten:**
1. eBay Developer Account erstellen
2. Sandbox API Keys erhalten
3. OAuth-Konfiguration einrichten

**Wo konfigurieren (später):**
- Google Secret Manager: `ebay_api_key`
- Google Secret Manager: `ebay_api_secret`
- Ambassador Agent Umgebungsvariablen

---

## 📝 Schritt-für-Schritt Anleitung

### Phase 1: Basis-Konfiguration (JETZT) ✅

**Status:** ✅ ABGESCHLOSSEN

#### 1. GCP Credentials ✅
```bash
# Bereits vorhanden:
- service-account-key.json
- true-campus-475614-p4-7ce543618d8d.json
```

#### 2. Dashboard Backend .env ✅
```bash
# Datei: dashboard/backend/.env
# Status: Basis-Konfiguration vollständig
# TODO: Optional GOOGLE_BOOKS_API_KEY hinzufügen
```

#### 3. Agent Konfigurationen ✅
```bash
# Bereits konfiguriert:
- agents/ingestion-agent/.env.yaml
- agents/condition-assessor/.env.yaml
```

---

### Phase 2: Optional Enhancements (BEI BEDARF)

#### 1. Google Books API Key hinzufügen

**Wenn gewünscht:**

1. **API Key erhalten:**
   ```bash
   # 1. Gehe zu GCP Console
   # 2. APIs & Services > Credentials
   # 3. Create Credentials > API Key
   # 4. Enable Books API
   ```

2. **In dashboard/backend/.env eintragen:**
   ```bash
   GOOGLE_BOOKS_API_KEY=dein-api-key-hier
   ```

3. **In agents/ingestion-agent/.env.yaml eintragen:**
   ```yaml
   GOOGLE_BOOKS_API_KEY: "dein-api-key-hier"
   ```

#### 2. Secret Manager für Production vorbereiten

**Für späteren Production Launch:**

```bash
# Encryption Key für User LLM Manager
gcloud secrets create user-llm-encryption-key \
  --data-file=- <<< "$(openssl rand -base64 32)"

# Optional: Google Books API Key
gcloud secrets create google-books-api-key \
  --data-file=- <<< "dein-api-key"
```

---

### Phase 3: Ambassador Agent Setup (SPÄTER)

#### Wann: Vor Aktivierung des Ambassador Agents

#### eBay API Configuration

1. **eBay Developer Account:**
   - Registrierung: https://developer.ebay.com/
   - Sandbox Account erstellen
   - Application erstellen

2. **API Keys in Secret Manager:**
   ```bash
   gcloud secrets create ebay-api-key \
     --data-file=- <<< "dein-ebay-api-key"
   
   gcloud secrets create ebay-api-secret \
     --data-file=- <<< "dein-ebay-api-secret"
   ```

3. **Ambassador Agent .env.yaml erstellen:**
   ```yaml
   EBAY_API_KEY: "aus-secret-manager"
   EBAY_API_SECRET: "aus-secret-manager"
   EBAY_ENVIRONMENT: "sandbox"  # Alpha nutzt Sandbox
   ```

---

## 🚀 Quick Start für Alpha Launch

### Minimal Setup (JETZT ausreichend):

✅ **Was bereits funktioniert:**
1. ✅ GCP Service Account konfiguriert
2. ✅ Firebase/Firestore läuft
3. ✅ Cloud Storage bereit
4. ✅ Dashboard Backend .env vorhanden
5. ✅ Agent .env.yaml Dateien vorhanden

✅ **Was du JETZT starten kannst:**
```bash
# 1. Backend starten
cd dashboard/backend
python main.py

# 2. Frontend starten
cd dashboard/frontend
npm run dev

# 3. Agents deployen (ohne eBay)
gcloud functions deploy ingestion-agent ...
gcloud functions deploy condition-assessor ...
```

⚠️ **Was OPTIONAL ist:**
- Google Books API Key (System läuft auch ohne)
- User LLM Keys (Über UI konfigurierbar)

❌ **Was SPÄTER kommt:**
- eBay API Keys (Erst bei Ambassador Aktivierung)

---

## 🔒 Security Best Practices

### ✅ Bereits implementiert:
- Service Account Keys in gitignore
- Firebase Authentication
- Firestore Security Rules
- CORS Configuration

### ⚠️ Für Production (später):
- [ ] Alle API Keys in Secret Manager
- [ ] Encryption Keys rotieren
- [ ] Rate Limiting implementiert
- [ ] VPC für Agents

---

## 📊 Configuration Matrix

| Component | .env Status | Required for Alpha | Notes |
|-----------|-------------|-------------------|-------|
| Dashboard Backend | ⚠️ Partial | ✅ Yes | Basis OK, API Keys optional |
| Ingestion Agent | ✅ Complete | ✅ Yes | Funktioniert |
| Condition Assessor | ✅ Complete | ✅ Yes | Funktioniert |
| Scout Agent | ➖ No .env | ✅ Yes | Nutzt GCP Env Vars |
| Strategist Agent | ➖ No .env | ❌ Not Yet | Phase 2 |
| Ambassador Agent | ❌ Missing | ❌ Not Yet | Phase 2 - braucht eBay |
| Sentinel Agent | ➖ No .env | ❌ Not Yet | Phase 2 |
| Sentinel Webhook | ➖ No .env | ❌ Not Yet | Phase 2 |

---

## ✅ Alpha Launch Checklist

### Sofort erforderlich:
- [x] GCP Service Account vorhanden
- [x] Dashboard Backend .env erstellt
- [x] Ingestion Agent .env.yaml vorhanden
- [x] Condition Assessor .env.yaml vorhanden
- [x] Cloud Storage Bucket konfiguriert
- [x] Firestore aktiviert

### Optional Enhancement:
- [ ] Google Books API Key hinzufügen
- [ ] Secret Manager vorbereiten
- [ ] User LLM Features testen

### Später (Phase 2):
- [ ] eBay API Keys beschaffen
- [ ] Ambassador Agent .env.yaml erstellen
- [ ] Strategist/Sentinel Agents aktivieren

---

## 🆘 Troubleshooting

### Problem: "Service Account not found"
**Lösung:** `service-account-key.json` ist vorhanden - verwende `GOOGLE_APPLICATION_CREDENTIALS`

### Problem: "Books API quota exceeded"
**Lösung:** Google Books API Key hinzufügen für höhere Limits

### Problem: "LLM Manager encryption error"
**Lösung:** ENCRYPTION_KEY wird automatisch aus Secret Manager geladen (für Alpha nicht kritisch)

---

## 📞 Nächste Schritte

1. ✅ **JETZT:** System mit Basis-Konfiguration starten
2. ⚠️ **BEI BEDARF:** Google Books API Key hinzufügen
3. ❌ **SPÄTER:** eBay Integration vorbereiten
4. 🚀 **DEPLOYMENT:** Alpha Version deployen

---

**Letzte Aktualisierung:** 2025-01-02
**Status:** Bereit für Alpha Launch (Basis-Features)
**Nächster Review:** Nach eBay Integration