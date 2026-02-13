# Plan zur Behebung des Deployment-Fehlers

## 1. Identifizierte Ursache

Das Deployment schlägt fehl, weil die verwendete WSL-Umgebung (Windows Subsystem for Linux) nicht korrekt konfiguriert ist. Es fehlen wesentliche Abhängigkeiten, die für die Ausführung des Deployment-Skripts erforderlich sind.

**Konkret wurden folgende Probleme in der Log-Datei [`ALPHA_DEPLOYMENT_LOG.md`](ALPHA_DEPLOYMENT_LOG.md:1) identifiziert:**
- **`python: not found`**: Das `gcloud` CLI-Tool, das für die Bereitstellung des Backends und der Agents verwendet wird, benötigt Python, kann es aber nicht finden.
- **`env: can't execute 'bash': No such file or directory`**: Das Skript zum Erstellen des Frontends konnte die `bash`-Shell nicht ausführen.
- **`node: not found`**: Das `firebase`-CLI-Tool, das für die Bereitstellung des Frontends verwendet wird, benötigt Node.js, kann es aber nicht finden.

## 2. Schritt-für-Schritt-Anleitung zur Behebung

Die folgenden Schritte müssen innerhalb Ihrer WSL-Distribution (z. B. Ubuntu) ausgeführt werden.

### Schritt 1: WSL-Umgebung aktualisieren

Stellen Sie sicher, dass Ihre Paketlisten auf dem neuesten Stand sind.

```bash
sudo apt update; sudo apt upgrade -y
```

### Schritt 2: Python installieren

Installieren Sie Python und das zugehörige Paket-Management-Tool `pip`. `gcloud` benötigt dies.

```bash
sudo apt install python3 python3-pip -y
```
Erstellen Sie einen Symlink, damit `python` auf `python3` verweist.
```bash
sudo ln -s /usr/bin/python3 /usr/bin/python
```

### Schritt 3: Node.js und npm installieren

Installieren Sie Node.js (wir empfehlen die LTS-Version) und npm. Dies wird für das Frontend-Deployment benötigt.

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Schritt 4: Firebase CLI installieren

Installieren Sie das Firebase-CLI-Tool global über npm.

```bash
npm install -g firebase-tools
```

### Schritt 5: Überprüfen der Installationen

Führen Sie die folgenden Befehle aus, um zu überprüfen, ob alle Tools korrekt installiert und im `PATH` verfügbar sind.

```bash
python --version
node --version
npm --version
firebase --version
gcloud --version
```
Wenn einer dieser Befehle einen Fehler wie "command not found" zurückgibt, ist die Installation oder die `PATH`-Konfiguration fehlgeschlagen.

## 3. Plan zur Überprüfung des Fixes

Nachdem Sie die obigen Schritte ausgeführt haben, führen Sie das Deployment-Skript erneut aus.

1.  **Starten Sie eine neue WSL-Shell**, um sicherzustellen, dass alle `PATH`-Änderungen übernommen wurden.
2.  Führen Sie das Deployment-Skript genau wie zuvor aus:
    ```bash
    ./deploy_alpha.sh
    ```
3.  **Überwachen Sie die Ausgabe.** Es sollten keine "not found"-Fehler mehr für `python`, `bash` oder `node` auftreten.
4.  **Überprüfen Sie die neue Log-Datei** (`ALPHA_DEPLOYMENT_LOG.md`), die generiert wird. Sie sollte keine der vorherigen Fehler mehr enthalten und am Ende einen Erfolgsstatus anzeigen.

## 4. Alternative Lösungswege

Falls die oben genannten Schritte nicht funktionieren:

- **WSL-Distribution neu installieren:** Manchmal ist eine WSL-Instanz beschädigt. Eine Neuinstallation kann das Problem beheben. Sichern Sie wichtige Daten, bevor Sie dies tun.
- **Docker verwenden:** Eine Alternative wäre, die gesamte Build- und Deployment-Pipeline in Docker-Containern auszuführen. Dies schafft eine konsistente und isolierte Umgebung, erfordert jedoch eine Anpassung des `deploy_alpha.sh`-Skripts.
