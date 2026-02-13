# End-to-End (E2E) Testplan: Mandantenfähige Architektur

## Testfall 1: Vollständiger Benutzer-Workflow und Datenisolierung

**Ziel:** Überprüfung des gesamten Workflows von der Benutzerregistrierung über den Upload eines Buches bis zur erfolgreichen Verarbeitung. Gleichzeitig wird die strikte Trennung der Daten zwischen zwei verschiedenen Benutzern verifiziert.

**Status:** `Bereit zum Testen`

**Voraussetzungen:**

1.  **Cloud-Infrastruktur:** Alle Backend-Dienste sind erfolgreich auf Cloud Run bereitgestellt.
2.  **Lokale Server:**
    *   `npm run dev` im `dashboard/frontend` Verzeichnis.
    *   `python main.py` im `dashboard/backend` Verzeichnis.
3.  **Tools:**
    *   Zwei verschiedene Browser oder Browser-Profile (z.B. Chrome Standard und Chrome Inkognito), um zwei Benutzer gleichzeitig zu simulieren.
    *   Google Cloud Console zur Beobachtung von Firestore-Daten und Cloud Run-Logs.
    *   Vorbereitete Testbilder.

**Schritte:**

**Teil A: Workflow für Benutzer 1**

1.  **Registrierung und Anmeldung (Benutzer 1):**
    *   Öffnen Sie Browser 1 und navigieren Sie zu `http://localhost:5173`.
    *   Registrieren Sie einen neuen Benutzer (z.B. `user1@test.com` mit Passwort `password`).
    *   Melden Sie sich als `user1@test.com` an. Die Buchliste sollte leer sein.

2.  **Buch-Upload (Benutzer 1):**
    *   Wählen Sie über die `ImageUpload`-Komponente ein oder mehrere Testbilder aus und laden Sie diese hoch.

3.  **Verarbeitungskette beobachten (Benutzer 1):**
    *   **Firestore:** Ein neues Dokument sollte in der `books`-Sammlung erscheinen. **Wichtig:** Überprüfen Sie, ob das Dokument ein `userId`-Feld enthält, das mit der Benutzer-ID von `user1@test.com` übereinstimmt.
    *   **Frontend (Benutzer 1):** Das neu erstellte Buch sollte in der `BookList` erscheinen.
    *   **`ingestion-agent` (Logs):** Beobachten Sie die Logs in der Cloud Console. Der Agent sollte die Verarbeitung des Buches bestätigen.
    *   **Firestore & Frontend:** Verfolgen Sie, wie der Status des Buches von `ingested` zu `identified` (oder einem anderen Endstatus) wechselt.

**Teil B: Datenisolierungstest mit Benutzer 2**

4.  **Registrierung und Anmeldung (Benutzer 2):**
    *   Öffnen Sie Browser 2 (oder das Inkognito-Fenster) und navigieren Sie zu `http://localhost:5173`.
    *   Registrieren Sie einen **anderen** neuen Benutzer (z.B. `user2@test.com` mit Passwort `password`).
    *   Melden Sie sich als `user2@test.com` an.

5.  **Überprüfung der Datenisolierung:**
    *   **Frontend (Benutzer 2):** Die Buchliste für `user2@test.com` **muss leer sein**. Es dürfen unter keinen Umständen die Bücher von `user1@test.com` angezeigt werden.
    *   **Firestore:** Führen Sie optional einen weiteren Upload für Benutzer 2 durch und überprüfen Sie, dass auch dieses Buch korrekt mit der `userId` von `user2@test.com` verknüpft wird.

**Erfolgskriterium:**

Der Test ist erfolgreich, wenn:
1.  Der gesamte Workflow für Benutzer 1 von der Registrierung bis zur Buchverarbeitung fehlerfrei funktioniert.
2.  Benutzer 2 nach der Anmeldung **keine** Daten von Benutzer 1 sehen kann, was die korrekte Datenisolierung bestätigt.