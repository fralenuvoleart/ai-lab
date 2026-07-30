#!/usr/bin/env bash
# ==============================================================================
# deploy.sh — Deploy AI-LAB workspace to remote Hetzner VPS via rsync
# Usage: bash scripts/deploy.sh [target-host]
# ==============================================================================
set -euo pipefail

TARGET="${1:-${DEPLOY_HOST:-}}"
REMOTE_USER="${DEPLOY_USER:-root}"
REMOTE_PATH="${DEPLOY_PATH:-/opt/ai-lab}"
EXCLUDE_FILE="$(dirname "$0")/../.gitignore"

if [ -z "$TARGET" ]; then
    echo "ERROR: No target host specified."
    echo "Usage: bash scripts/deploy.sh user@host"
    echo "   or: DEPLOY_HOST=user@host bash scripts/deploy.sh"
    exit 1
fi

DRY_RUN=""
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN="--dry-run"
    echo "🔍 DRY RUN — no changes will be made"
    shift
    TARGET="${1:-${DEPLOY_HOST:-}}"
fi

echo "🚀 Deploying to ${REMOTE_USER}@${TARGET}:${REMOTE_PATH} ..."

# === STEP 1: Pull knowledge assets FROM server (backup direction) ===
echo "📥 Pulling knowledge assets from server (backup)..."
rsync -avzu ${REMOTE_USER}@${TARGET}:${REMOTE_PATH}/data/vault/ "$(dirname "$0")/../data/vault/" || true
rsync -avzu ${REMOTE_USER}@${TARGET}:${REMOTE_PATH}/data/open-webui/webui.db "$(dirname "$0")/../projects/open-webui/data/" || true
rsync -avzu ${REMOTE_USER}@${TARGET}:${REMOTE_PATH}/data/open-webui/uploads/ "$(dirname "$0")/../projects/open-webui/data/uploads/" || true

# === STEP 2: Push code + configs TO server (deploy direction) ===
echo "📤 Pushing code and configs to server (deploy)..."
rsync -avz ${DRY_RUN} --delete \
    --exclude-from="${EXCLUDE_FILE}" \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='*.log' \
    --exclude='infra/postgres/data/' \
    --exclude='infra/qdrant/storage/' \
    --exclude='projects/*/data/' \
    --exclude='secrets/' \
    --exclude='data/vault/' \
    --exclude='shared/venv-*/' \
    "$(dirname "$0")/../" \
    "${REMOTE_USER}@${TARGET}:${REMOTE_PATH}"

echo ""
echo "✅ Deploy complete."
echo "   📥 Knowledge assets pulled from server (backup)."
echo "   📤 Code + configs pushed to server (deploy)."
echo "   🔐 If configs or secrets changed, run: bash scripts/deploy-config.sh"
echo "   SSH into target: ssh ${REMOTE_USER}@${TARGET}"
echo "   Start infra:     cd ${REMOTE_PATH} && make infra-up"
