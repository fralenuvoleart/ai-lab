#!/usr/bin/env bash
# ==============================================================================
# backup-db.sh — Backup PostgreSQL databases to compressed SQL dumps
# Usage: bash scripts/backup-db.sh
# ==============================================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP="$(date +%Y-%m-%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/ailab-backup-${TIMESTAMP}.sql.gz"
COMPOSE_FILE="$(dirname "$0")/../infra/docker-compose.infra.yml"

# Load env vars
if [ -f "$(dirname "$0")/../.env" ]; then
    set -a
    source "$(dirname "$0")/../.env"
    set +a
fi

DB_USER="${POSTGRES_USER:-ailab}"
DB_NAME="${POSTGRES_DB:-ailab}"

mkdir -p "${BACKUP_DIR}"

echo "📦 Backing up database '${DB_NAME}' to ${BACKUP_FILE} ..."

docker compose -f "${COMPOSE_FILE}" exec -T postgres \
    pg_dump -U "${DB_USER}" -d "${DB_NAME}" --no-owner --no-acl \
    | gzip > "${BACKUP_FILE}"

# Verify backup integrity
if [ "${PIPESTATUS[0]}" -ne 0 ]; then
    echo "❌ pg_dump failed — backup may be incomplete"
    rm -f "${BACKUP_FILE}"
    exit 1
fi
sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"

echo "✅ Backup complete: ${BACKUP_FILE}"
echo "   Size: $(du -h "${BACKUP_FILE}" | cut -f1)"

# Cleanup old backups (keep last 7 days)
find "${BACKUP_DIR}" -name "ailab-backup-*.sql.gz" -mtime +7 -delete 2>/dev/null || true
echo "   Cleaned backups older than 7 days."
