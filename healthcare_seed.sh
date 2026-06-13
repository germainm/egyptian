#!/usr/bin/env bash
# healthcare_seed.sh — Initialise et peuple un Mayan EDMS Healthcare depuis Docker.
#
# Prérequis : être dans le répertoire contenant docker-compose.yml, stack démarrée.
#
# Usage :
#   bash healthcare_seed.sh
#
# Variables d'environnement :
#   DC   — commande docker compose  (défaut : "docker compose")
#   APP  — nom du service app       (défaut : "app")

set -euo pipefail

DC="${DC:-docker compose}"
APP="${APP:-app}"

# ── Détection de mayan-edms.py dans le conteneur ────────────────────────────
MAYAN=$($DC exec -T "$APP" \
    find /opt -name "mayan-edms.py" -not -name "*.pyc" 2>/dev/null \
    | head -1 | tr -d '\r\n')

if [ -z "$MAYAN" ]; then
    echo "ERREUR : mayan-edms.py introuvable dans le conteneur '$APP'." >&2
    echo "Vérifier que le conteneur est démarré : $DC ps" >&2
    exit 1
fi

echo "mayan-edms.py : $MAYAN"
echo ""

# ── Étape 1 : health_init ────────────────────────────────────────────────────
echo "════════════════════════════════════════════════════════════"
echo "  Étape 1/2 — health_init"
echo "════════════════════════════════════════════════════════════"
$DC exec "$APP" "$MAYAN" health_init

echo ""

# ── Étape 2 : health_seed ────────────────────────────────────────────────────
echo "════════════════════════════════════════════════════════════"
echo "  Étape 2/2 — health_seed  (documents + tâches + index)"
echo "════════════════════════════════════════════════════════════"
$DC exec "$APP" "$MAYAN" health_seed
