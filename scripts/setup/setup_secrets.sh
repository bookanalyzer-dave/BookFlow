#!/bin/bash

# Dieses Skript richtet Platzhalter-Secrets im Google Secret Manager ein.
# WICHTIG: Nachdem Sie dieses Skript ausgeführt haben, müssen Sie die
# Platzhalterwerte manuell mit Ihren tatsächlichen geheimen Schlüsseln in der Google Cloud Console aktualisieren.

# --- eBay-Authentifizierungstoken ---
# Beschreibung: Dieses Secret speichert das Authentifizierungstoken für die eBay-API.
echo "Erstelle eBay-Auth-Token-Secret..."
gcloud secrets create ebay-auth-token --replication-policy="automatic"
printf "EBAY_AUTH_TOKEN_PLACEHOLDER" | gcloud secrets versions add ebay-auth-token --data-file=-
echo "eBay-Auth-Token-Secret mit einem Platzhalterwert erstellt."
echo "Bitte aktualisieren Sie es mit Ihrem tatsächlichen Token."
echo ""

# --- Amazon-Authentifizierungstoken ---
# Beschreibung: Dieses Secret speichert das Authentifizierungstoken für die Amazon-API.
echo "Erstelle Amazon-Auth-Token-Secret..."
gcloud secrets create amazon-auth-token --replication-policy="automatic"
printf "AMAZON_AUTH_TOKEN_PLACEHOLDER" | gcloud secrets versions add amazon-auth-token --data-file=-
echo "Amazon-Auth-Token-Secret mit einem Platzhalterwert erstellt."
echo "Bitte aktualisieren Sie es mit Ihrem tatsächlichen Token."
echo ""

echo "Secret-Setup abgeschlossen."