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

echo "🚀 Deploying to ${REMOTE_USER}@${TARGET}:${REMOTE_PATH} ..."

rsync -avz --delete \
    --exclude-from="${EXCLUDE_FILE}" \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='*.log' \
    --exclude='infra/postgres/data/' \
    --exclude='infra/qdrant/storage/' \
    "$(dirname "$0")/../" \
    "${REMOTE_USER}@${TARGET}:${REMOTE_PATH}"

echo ""
echo "✅ Deploy complete."
echo "   SSH into target: ssh ${REMOTE_USER}@${TARGET}"
echo "   Start infra:     cd ${REMOTE_PATH} && make infra-up"
