#!/usr/bin/env bash
# ==============================================================================
# deploy-config.sh — Install configs + secrets to server locations
# Run AFTER deploy.sh, only when configs or secrets changed.
# Usage: bash scripts/deploy-config.sh [target-host]
# ==============================================================================
set -euo pipefail

TARGET="${1:-${DEPLOY_HOST:-}}"
REMOTE_PATH="${DEPLOY_PATH:-/opt/ai-lab}"

if [ -z "$TARGET" ]; then
    echo "ERROR: No target host specified."
    echo "Usage: bash scripts/deploy-config.sh user@host"
    echo "   or: DEPLOY_HOST=user@host bash scripts/deploy-config.sh"
    exit 1
fi

echo "🔧 Deploying configs to ${TARGET} ..."

SCRIPT_DIR="$(dirname "$0")/.."

# === SearXNG — real files (not symlinks) ===
echo "  → SearXNG configs..."
scp "${SCRIPT_DIR}/config/searxng/docker-compose.yml" "root@${TARGET}:/opt/searxng/"
scp "${SCRIPT_DIR}/config/searxng/mcp_server.py" "root@${TARGET}:/opt/searxng/"

# === Systemd — clean units (no secrets) ===
echo "  → Systemd units..."
scp "${SCRIPT_DIR}/config/systemd/basic-memory.service" "root@${TARGET}:/etc/systemd/system/"
scp "${SCRIPT_DIR}/config/systemd/ollama.service" "root@${TARGET}:/etc/systemd/system/"

# === Secrets — to their actual server locations ===
echo "  → Secrets..."
scp "${SCRIPT_DIR}/secrets/mcpo-tools.json" "root@${TARGET}:/root/.mcpo-tools.json"
scp "${SCRIPT_DIR}/secrets/mcp-tools.service" "root@${TARGET}:/etc/systemd/system/"
scp "${SCRIPT_DIR}/secrets/telegram-bot.service" "root@${TARGET}:/etc/systemd/system/"
scp "${SCRIPT_DIR}/secrets/open-webui.env" "root@${TARGET}:${REMOTE_PATH}/projects/open-webui/.env"
scp "${SCRIPT_DIR}/secrets/basic-memory-config.json" "root@${TARGET}:/root/.basic-memory/config.json"

# === Reload systemd and restart affected services ===
echo "  → Reloading systemd and restarting services..."
ssh "root@${TARGET}" << 'ENDSSH'
systemctl daemon-reload
systemctl restart basic-memory
systemctl restart mcp-tools
cd /opt/searxng && docker compose restart searxng
echo "  ✓ Config deployment complete."
ENDSSH

echo ""
echo "✅ Configs + secrets deployed and services restarted."
