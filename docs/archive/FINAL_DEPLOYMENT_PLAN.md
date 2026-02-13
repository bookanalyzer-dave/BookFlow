# Finaler Deployment-Plan

**Datum:** 2025-11-01

## 1. Staging-Deployment

### Ziele:
- Verifizierung der Deployment-Skripte in einer produktionsnahen Umgebung.
- Durchführung von finalen manuellen Tests.
- Sicherstellung, dass alle Konfigurationen und Secrets korrekt geladen werden.

### Schritte:
1.  **Infrastruktur aufbauen:** Alle Befehle aus dem Abschnitt `Infrastructure Deployment` der [`DEPLOYMENT_COMMANDS.md`](DEPLOYMENT_COMMANDS.md) ausführen.
2.  **Secrets konfigurieren:** Alle erforderlichen Secrets im Secret Manager anlegen.
3.  **Agenten bereitstellen:** Alle Agenten und das Dashboard-Backend gemäß den `DEPLOYMENT_COMMANDS.md` in der Staging-Umgebung bereitstellen.
4.  **Manuelle Verifizierung:** Einen vollständigen End-to-End-Test manuell durchführen:
    -   Benutzer registrieren und anmelden.
    -   Bilder hochladen.
    -   Den Verarbeitungs-Workflow in Firestore verfolgen.
    -   Überprüfen, ob alle Agenten wie erwartet ausgelöst werden.

## 2. Produktions-Deployment

### Ziele:
- Zero-Downtime-Deployment des Systems.
- Aktivierung von Monitoring und Alerting.
- Sicherstellung der Systemstabilität nach dem Launch.

### Schritte:
1.  **Backup:** Ein finales Backup der Firestore-Datenbank erstellen.
2.  **Deployment:** Die gleichen Schritte wie beim Staging-Deployment in der Produktionsumgebung ausführen.
3.  **Monitoring aktivieren:** Sicherstellen, dass die in den `DEPLOYMENT_COMMANDS.md` definierten Uptime-Checks und Alert-Policies aktiv sind.
4.  **Post-Launch-Checkliste:** Die `Post-Deployment Checklist` in den `DEPLOYMENT_COMMANDS.md` abarbeiten.

## 3. Rollback-Plan

Im Falle eines kritischen Fehlers während des Deployments wird der folgende Rollback-Plan ausgeführt:
1.  **Cloud Run Services:** Die vorherige Revision des fehlerhaften Dienstes wird sofort wieder aktiviert.
2.  **Firestore-Regeln:** Die vorherige Version der `firestore.rules` wird aus der Git-Historie wiederhergestellt und erneut bereitgestellt.
3.  **Datenbank:** Bei Datenkorruption wird das vor dem Deployment erstellte Backup wiederhergestellt.
