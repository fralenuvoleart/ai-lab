#!/usr/bin/env bash
# ==============================================================================
# backup-full.sh — Full AI Lab stack backup
# Usage: bash scripts/backup-full.sh
# Restore: see RESTORE section at bottom of this file
# ==============================================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/backups}"
TIMESTAMP="$(date +%Y-%m-%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/ailab-full-${TIMESTAMP}.tar.gz"

mkdir -p "${BACKUP_DIR}"

echo "📦 Creating full backup: ${BACKUP_FILE}"

tar -czf "${BACKUP_FILE}" \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='__pycache__' \
    /data/vault \
    /opt/ai-lab/projects/open-webui/data/webui.db \
    /opt/ai-lab/.env \
    /opt/ai-lab/projects/open-webui/.env \
    /root/.basic-memory/config.json \
    /root/.basic-memory/memory.db \
    /root/.mcpo-tools.json \
    /etc/systemd/system/basic-memory.service \
    /etc/systemd/system/mcp-tools.service \
    /opt/ai-lab/infra/caddy/Caddyfile \
    2>/dev/null

echo "✅ Backup complete: ${BACKUP_FILE}"
echo "   Size: $(du -h "${BACKUP_FILE}" | cut -f1)"

# Keep last 7 daily backups
find "${BACKUP_DIR}" -name "ailab-full-*.tar.gz" -mtime +7 -delete 2>/dev/null || true
echo "   Cleaned backups older than 7 days."

# ==============================================================================
# RESTORE INSTRUCTIONS
# ==============================================================================
# 1. Set up Hetzner VPS (Ubuntu, Docker, SSH key)
# 2. Clone/rsync workspace to /opt/ai-lab
# 3. Extract backup: tar -xzf ailab-full-*.tar.gz -C /
# 4. Start infra:  cd /opt/ai-lab && docker compose -f infra/docker-compose.infra.yml up -d
# 5. Start Open WebUI: cd /opt/ai-lab/projects/open-webui && docker compose up -d
# 6. Install pipx packages: pipx install basic-memory mcpo mcp-server-fetch
# 7. Start MCP services: systemctl enable --now basic-memory mcp-tools
# 8. Verify: curl http://localhost:8000/openapi.json
# ==============================================================================
