# 📚 Dokumentations-Index

Willkommen zur strukturierten Projektdokumentation. Diese Übersicht dient als zentraler Einstiegspunkt für alle technischen und organisatorischen Informationen.

## 🗂️ Dokumentations-Struktur

### 📄 [current/](./current/) - Aktuelle Kerndokumentation (SSOT)
Dies ist die **Single Source of Truth** für die aktuelle Systemarchitektur und Konfiguration.

- **[TECHNICAL_ARCHITECTURE.md](./current/TECHNICAL_ARCHITECTURE.md)** - Vollständige technische Architektur-Dokumentation.
- **[PROJECT_STRUCTURE.md](./current/PROJECT_STRUCTURE.md)** - Übersicht der Dateistruktur und Modul-Zuständigkeiten.
- **[CONFIGURATION_REFERENCE.md](./current/CONFIGURATION_REFERENCE.md)** - Umfassende Konfigurations-Referenz für alle Komponenten.

### 🤖 [agents/](./agents/) - Agent-Dokumentation
Detaillierte Dokumentation zu den intelligenten Agenten und deren KI-Integration.

- **[INGESTION_AGENT.md](./agents/INGESTION_AGENT.md)** - Vollständige Referenz des Ingestion Agents.
- **[AGENTS_DEEP_DIVE.md](./agents/AGENTS_DEEP_DIVE.md)** - Ausführliche technische Beschreibung aller Agenten.
- **[CONDITION_ASSESSOR.md](./agents/CONDITION_ASSESSOR.md)** - Spezifikationen für den Condition Assessment Agent.
- **[STRATEGIST_AGENT.md](./agents/STRATEGIST_AGENT.md)** - Spezifikationen für den Strategist Agent.
- **[USER_LLM_MANAGEMENT_DOCUMENTATION.md](./agents/USER_LLM_MANAGEMENT_DOCUMENTATION.md)** - Benutzerverwaltung für LLM-Credentials.

### 🚀 [deployment/](./deployment/) - Deployment-Guides
Anleitungen für das Deployment auf Google Cloud Platform.

- **[PRODUCTION_DEPLOYMENT_GUIDE.md](./deployment/PRODUCTION_DEPLOYMENT_GUIDE.md)** - Aktueller Guide für das produktive Deployment.
- **[GCP_MIGRATION_GUIDE.md](../docs/guides/GCP_MIGRATION_GUIDE.md)** - Leitfaden für Infrastruktur-Migrationen.

### 📊 [reports/](./reports/) - Berichte & Protokolle
Sammlung von Berichten zu Tests, Deployments und Systemänderungen (Berichte).

- **[DOCUMENTATION_CLEANUP_2026-02-04.md](./reports/DOCUMENTATION_CLEANUP_2026-02-04.md)** - Protokoll der Dokumentationsbereinigung.
- **[TOPIC_RENAMING_AND_DLQ_IMPLEMENTATION_2026-02-04.md](./reports/TOPIC_RENAMING_AND_DLQ_IMPLEMENTATION_2026-02-04.md)** - Bericht zur Pub/Sub Umstellung.
- **[DEPLOYMENT_FIXES_REPORT_2026-01-19.md](./reports/DEPLOYMENT_FIXES_REPORT_2026-01-19.md)** - Analyse früherer Deployment-Fixes.

### ⚙️ [operations/](./operations/) - Betrieb & Wartung
Dokumentation für den laufenden Betrieb.

- **[OPERATIONS_RUNBOOK.md](./operations/OPERATIONS_RUNBOOK.md)** - Operatives Handbuch für Monitoring und Troubleshooting.
- **[START_COMMANDS.md](./operations/START_COMMANDS.md)** - Referenz der wichtigsten Start-Befehle.

### 🧪 [testing/](./testing/) - Testing-Dokumentation
Test-Strategie, Validierungs-Befehle und Reports.

- **[VALIDATION_COMMANDS.md](./testing/VALIDATION_COMMANDS.md)** - Befehle zur System-Validierung.
- **[LIVE_SIMULATION_REPORT_2026-01-30.md](./testing/LIVE_SIMULATION_REPORT_2026-01-30.md)** - Ergebnisse der Live-Simulation.
- **[E2E_TESTING.md](./testing/E2E_TESTING.md)** - End-to-End Test-Strategie.

### 📦 [archive/](./archive/) - Archiv (Historie)
Veraltete Dokumente, Protokolle früherer Phasen und historische Pläne.

---

## 🔍 Schnellzugriff

### Für neue Entwickler:
1. Starte mit [../README.md](../README.md) - Projekt-Übersicht.
2. Lies [current/TECHNICAL_ARCHITECTURE.md](./current/TECHNICAL_ARCHITECTURE.md) - Architektur verstehen.
3. Konsultiere [agents/AGENTS_DEEP_DIVE.md](./agents/AGENTS_DEEP_DIVE.md) - Agenten verstehen.

### Für Deployment & Betrieb:
1. [deployment/PRODUCTION_DEPLOYMENT_GUIDE.md](./deployment/PRODUCTION_DEPLOYMENT_GUIDE.md) - Produktion-Setup.
2. [operations/OPERATIONS_RUNBOOK.md](./operations/OPERATIONS_RUNBOOK.md) - Fehlersuche & Betrieb.
3. [testing/VALIDATION_COMMANDS.md](./testing/VALIDATION_COMMANDS.md) - System prüfen.

---

## 📝 Dokumentations-Richtlinien

- **Aktive Dokumente (SSOT)** gehören nach `docs/current/`.
- **Berichte & Reports** werden in `docs/reports/` abgelegt.
- **Veraltete Dokumente** werden in das `archive/` verschoben, um die Übersichtlichkeit zu wahren.
- Alle neuen Dokumente sollten dem etablierten Markdown-Style folgen.

---

*Letzte Aktualisierung: 2026-02-04*
