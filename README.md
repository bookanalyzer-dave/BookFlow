# 📚 Intelligent Book Sales Pipeline

> Vollautomatisierte AI-gestützte Plattform für Bucherfassung, -analyse und -verkauf über Online-Marktplätze

[![Status](https://img.shields.io/badge/Status-Alpha%20Ready-green)](PROJECT_STATUS.md)
[![GCP](https://img.shields.io/badge/GCP-Cloud%20Run-blue)](https://cloud.google.com/run)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-blue)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red)]()

---

## 🎯 Projekt-Übersicht

Das **Intelligent Book Sales Pipeline** ist ein Cloud-natives System, das den kompletten Buchverkaufs-Prozess automatisiert - von der Bilderfassung bis zum Online-Verkauf. Mit Hilfe von modernster KI (Vertex AI, OpenAI, Anthropic) analysiert das System Buchzustand, ermittelt optimale Preise und erstellt automatisch Marktplatz-Listings.

### ✨ Highlights

- 🤖 **7 Spezialisierte AI-Agents** - Event-driven Microservices Architecture
- 🔐 **Multi-Tenant von Grund auf** - Vollständige Datenisolation zwischen Benutzern
- 🌟 **System-Level LLM Integration** - Zentral gesteuerte Gemini AI Integration für alle Agents
- 📊 **Real-time Monitoring** - Überwachung von Agent-Performance und API-Usage
- 🎨 **Modern Dashboard** - React-basierte UI mit Firebase Auth
- 🛡️ **Production-Grade Security** - AES-256 Encryption, Audit Logging, Security Rules

### 🚀 Current Status

**Version:** 1.0.0-alpha
**Status:** ✅ **PRODUCTION READY** - Ingestion Agent deployed & tested
**User Capacity:** Limited (Alpha Testing)
**GCP Project:** project-52b2fab8-15a1-4b66-9f3
**Deployment Details:** See [`PROJECT_STATUS.md`](PROJECT_STATUS.md)

---

## 📋 Features

### Core Features

- ✅ **Intelligente Buchidentifikation** via Vertex AI Vision
- ✅ **Automatische Zustandsbeurteilung** (New → Acceptable)
- ✅ **Dynamische Preisgestaltung** basierend auf Marktdaten
- ✅ **Multi-Platform Listings** (aktuell: eBay, erweiterbar)
- ✅ **Automatic Sale Handling** & Cross-Platform Delisting
- ✅ **Real-time Dashboard** mit Live-Updates

### 🌟 System-Level LLM Integration

Das System nutzt eine zentrale Gemini-Integration auf System-Ebene für maximale Stabilität und Performance:

- **Zentrales API-Management**: Nutzung von `GEMINI_API_KEY` für alle Agent-Interaktionen
- **Skalierbarkeit**: Optimierte Nutzung der Google Vertex AI / GenAI Infrastruktur
- **Vereinfachte Konfiguration**: Keine individuelle User-LLM-Verwaltung mehr notwendig

---

## 🏗️ Architektur

### High-Level Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Browser   │────▶│   Dashboard  │────▶│  Firebase   │
│             │     │   (React)    │     │    Auth     │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Backend    │
                    │   (Flask)    │
                    └──────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐      ┌──────────┐      ┌──────────┐
   │Firestore│      │  Cloud   │      │ Pub/Sub  │
   │         │      │ Storage  │      │          │
   └─────────┘      └──────────┘      └──────────┘
                                             │
                    ┌────────────────────────┤
                    ▼                        ▼
              ┌───────────┐           ┌───────────┐
              │  Agents   │           │  Agents   │
              │ (Cloud Run)│          │ (Cloud Run)│
              └───────────┘           └───────────┘
```

### Technology Stack

**Frontend:**
- React 18 + Vite
- Firebase Authentication
- Modern CSS

**Backend:**
- Python 3.11/3.12
- Flask + Flask-CORS + Flask-Limiter
- Firebase Admin SDK

**Infrastructure:**
- Google Cloud Platform (GCP)
- Cloud Run (Auto-Scaling)
- Cloud Functions (Event-Driven)
- Firestore (Native Mode)
- Cloud Storage
- Pub/Sub
- Vertex AI

**AI/ML:**
- Vertex AI (Gemini 2.0 Flash)
- OpenAI API (GPT-4o, GPT-4o-mini)
- Anthropic API (Claude 3.5 Sonnet)
- Google Books API

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 oder 3.12
- Node.js 18+
- GCP Account
- Firebase Project
- Git

### Installation

1. **Clone Repository**
   ```bash
   git clone https://github.com/your-org/intelligent-book-sales-pipeline.git
   cd intelligent-book-sales-pipeline
   ```

2. **Backend Setup**
   ```bash
   cd dashboard/backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # .env ausfüllen mit GEMINI_API_KEY, Firebase & GCP Credentials
   python main.py
   ```

3. **Frontend Setup**
   ```bash
   cd dashboard/frontend
   npm install
   npm run dev
   ```

4. **Access Dashboard**
   - Open http://localhost:5173
   - Register new account
   - Upload book images
   - Configure LLM settings (optional)

### Deployment

Siehe detaillierte Anweisungen in [`docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md`](docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md)

```bash
# Complete Deployment
gcloud builds submit --config=cloudbuild.yaml

# Verify Deployment
bash QUICK_REFERENCE.md  # Health Check Section
```

---

## 📚 Documentation

> **📖 Vollständige Dokumentation:** [`docs/README.md`](docs/README.md) - Strukturierter Index aller Dokumente

### 📂 Struktur-Übersicht

- **`docs/current/`**: Single Source of Truth (SSOT). Aktuelle Architektur, Konfiguration und Guides.
- **`docs/agents/`**: Spezifische Dokumentation zu den einzelnen AI-Agents.
- **`docs/reports/`**: Berichte zu Tests, Deployments und Debugging-Sessions.
- **`docs/archive/`**: Veraltete oder historische Dokumente (Referenz).

### 🚀 Schnellstart-Dokumente

| Dokument | Beschreibung |
|----------|--------------|
| [`PROJECT_STATUS.md`](PROJECT_STATUS.md) | **Aktueller Projektstatus & Übersicht** |
| [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md) | One-Pager mit wichtigsten Commands |
| [`docs/current/TECHNICAL_ARCHITECTURE.md`](docs/current/TECHNICAL_ARCHITECTURE.md) | Vollständige technische Architektur |
| [`docs/current/CONFIGURATION_REFERENCE.md`](docs/current/CONFIGURATION_REFERENCE.md) | Konfigurations-Referenz |

### 🤖 Agents & Features

| Dokument | Beschreibung |
|----------|--------------|
| [`docs/agents/AGENTS_DEEP_DIVE.md`](docs/agents/AGENTS_DEEP_DIVE.md) | Detaillierte Agent-Dokumentation |
| [`docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md`](docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md) | Production Deployment Guide |

### 🚀 Deployment & Operations

| Dokument | Beschreibung |
|----------|--------------|
| [`docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md`](docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md) | Production Deployment Guide |
| [`docs/operations/OPERATIONS_RUNBOOK.md`](docs/operations/OPERATIONS_RUNBOOK.md) | Troubleshooting & Operations |
| [`docs/operations/START_COMMANDS.md`](docs/operations/START_COMMANDS.md) | Development Setup Commands |

### 🧪 Testing & Quality

| Dokument | Beschreibung |
|----------|--------------|
| [`docs/testing/E2E_TEST_REPORT.md`](docs/testing/E2E_TEST_REPORT.md) | E2E Test Results & Findings |
| [`docs/testing/E2E_TESTING.md`](docs/testing/E2E_TESTING.md) | Testing Strategy |
| [`docs/current/FIX_LOG.md`](docs/current/FIX_LOG.md) | Code Fix Protocol |

---

## 🤖 Agents

Das System besteht aus 6 spezialisierten AI-Agents (Scribe ist in Ingestion integriert):

| Agent | Status | Trigger | Hauptfunktion |
|-------|--------|---------|---------------|
| **Ingestion Agent** | ✅ **DEPLOYED** | Pub/Sub: `trigger-ingestion` | Buchidentifikation, Anreicherung via Google Books API, AI-Beschreibung |
| **Condition Assessor** | ⚠️ **CODE READY** | Firestore onCreate: `condition_assessment_requests` | Multi-Image Zustandsanalyse mit Vertex AI Vision |
| **Strategist Agent** | ⚠️ **CODE READY** | Pub/Sub (nach Condition Assessment) | Marktdatenanalyse & dynamische Preisberechnung |
| **Ambassador Agent** | ⚠️ **CODE READY** | Pub/Sub: `list-book-request` | eBay Listing Creation & Management (eBay Credentials fehlen) |
| **Sentinel Agent** | ⚠️ **CODE READY** | Pub/Sub: `sale-notification-received` | Sale Notifications & Auto-Delisting Orchestrierung |
| **Scout Agent** | ⚠️ **CODE READY** | HTTP /scrape (optional) | Competitor Price Collection via Web Scraping |

**Hinweis:** Scribe Agent wurde vollständig in Ingestion Agent integriert

**Details:** [`docs/agents/AGENTS_DEEP_DIVE.md`](docs/agents/AGENTS_DEEP_DIVE.md)

---

## 🧪 Testing

### Run Tests

```bash
# Unit Tests
pytest shared/ --cov

# Integration Tests
python extended_integration_test.py

# E2E Tests
python comprehensive_e2e_test.py

# Frontend E2E (Playwright)
cd dashboard/frontend
npx playwright test
```

### Test Results

- **Unit Tests**: ⚠️ Coverage <50% (ausbaufähig)
- **Integration Tests**: ✅ Alle Tests erfolgreich (100% bestanden)
- **E2E Tests**: ✅ Alle Tests erfolgreich (100% bestanden)
- **Load Tests**: ❌ Noch nicht durchgeführt

**Details:** [`docs/testing/E2E_TEST_REPORT.md`](docs/testing/E2E_TEST_REPORT.md)

---

## 📊 Project Status

### Deployment Readiness

| Launch Phase | Status | User Capacity | Timeline |
|--------------|--------|---------------|----------|
| **Alpha** | ✅ READY | 10-50 | Jetzt (nach 4-6h Setup) |
| **Beta** | ⚠️ 1-2 Wochen | 100-500 | Nach Load Testing |
| **GA** | ❌ 4-6 Wochen | 1000+ | Nach Security Audit |

### Known Issues

| Issue | Severity | Impact | Required For |
|-------|----------|--------|--------------|
| Load Testing nicht durchgeführt | 🔴 HIGH | Unbekannte Performance | Beta |
| eBay Production API nicht getestet | 🔴 HIGH | Listings könnten fehlschlagen | Beta |
| Pricing Algorithm nicht validiert | 🔴 HIGH | Suboptimale Preise | Beta |
| Description Quality Metrics fehlen | 🟡 MEDIUM | Keine QA | GA |
| Single Marketplace (nur eBay) | 🟡 MEDIUM | Limitierte Kanäle | Phase 2 |

**Vollständige Liste:** [`docs/testing/E2E_TEST_REPORT.md`](docs/testing/E2E_TEST_REPORT.md)

---

## 🛣️ Roadmap

### Phase 2: Feature Expansion (Post-Alpha)
- Multi-Marketplace Support (Amazon, AbeBooks)
- Advanced Analytics Dashboard
- Bulk Upload Functionality
- Template-basierte Listings

### Phase 3: Enterprise Features (Post-Beta)
- Team Accounts & Shared Credentials
- Role-Based Access Control (RBAC)
- Advanced ML Pricing Models
- Mobile App (iOS/Android)

### Phase 4: Scale & Optimize (Post-GA)
- Multi-Region Deployment
- CDN Integration
- Advanced Caching
- Webhook API for 3rd-party Integration

---

## 🤝 Contributing

### Development Guidelines

1. **Code Style**: Follow PEP 8 (Python), ESLint (JavaScript)
2. **Testing**: Write tests for new features
3. **Documentation**: Update relevant docs
4. **Security**: No secrets in code, use Secret Manager

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Production hotfixes

### Pull Request Process

1. Create feature branch from `develop`
2. Write tests for new code
3. Update documentation
4. Submit PR with description
5. Pass code review
6. Merge to `develop`

---

## 📞 Support

### Documentation

- **Quick Reference**: [`QUICK_REFERENCE.md`](QUICK_REFERENCE.md)
- **Operations Guide**: [`docs/operations/OPERATIONS_RUNBOOK.md`](docs/operations/OPERATIONS_RUNBOOK.md)
- **Documentation Index**: [`docs/README.md`](docs/README.md)

### Resources

- **GCP Console**: https://console.cloud.google.com/home/dashboard?project=project-52b2fab8-15a1-4b66-9f3
- **Cloud Run**: https://console.cloud.google.com/run?project=project-52b2fab8-15a1-4b66-9f3
- **Firestore**: https://console.cloud.google.com/firestore?project=project-52b2fab8-15a1-4b66-9f3
- **Cloud Logging**: https://console.cloud.google.com/logs?project=project-52b2fab8-15a1-4b66-9f3

### Contacts

- **Project Lead**: [TBD]
- **DevOps Lead**: [TBD]
- **On-Call (Alpha)**: Manual monitoring only

---

## 📜 License

Proprietary - All Rights Reserved

---

## 🙏 Acknowledgments

**Technologies:**
- Google Cloud Platform
- Firebase
- Vertex AI
- OpenAI
- Anthropic
- React
- Flask

**Built with:** ❤️ and ☕

---

**Version:** 1.0.0-alpha
**Last Updated:** 2026-02-04
**Status:** ✅ INGESTION AGENT PRODUCTION-READY (Refactored to System LLM)
**Next Milestone:** Test complete book ingestion workflow, then deploy remaining agents

---

## 🔗 Quick Links

- 📖 [Documentation Index](docs/README.md)
- 📊 [Project Status](PROJECT_STATUS.md)
- 🏗️ [Technical Architecture](docs/current/TECHNICAL_ARCHITECTURE.md)
- 🚀 [Deployment Guide](docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md)
- 🛠️ [Operations Runbook](docs/operations/OPERATIONS_RUNBOOK.md)
- ⚡ [Quick Reference](QUICK_REFERENCE.md)

**Ready to test?** See [`docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md`](docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md) for production setup.
