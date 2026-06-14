#!/bin/bash
set -euo pipefail
# Daily Postgres backup for Business Radar AI.
#
# Usage:
#   ./scripts/backup_db.sh              # writes to $BACKUP_LOCAL_DIR
#   BACKUP_S3_TARGET=s3://my-bucket/path ./scripts/backup_db.sh   # uploads to S3 (needs aws cli)
#
# Retention is BACKUP_RETENTION_DAYS days (local copies).

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
set -a; source "$ROOT/.env" 2>/dev/null || true; set +a

DATE="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="${BACKUP_LOCAL_DIR:-$ROOT/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
mkdir -p "$BACKUP_DIR"

DB_URL="${DATABASE_URL_SYNC:-${DATABASE_URL:-}}"
DB_URL="${DB_URL/+asyncpg/}"
if [ -z "$DB_URL" ]; then
  echo "DATABASE_URL not set" >&2; exit 1
fi

OUT="$BACKUP_DIR/businessradar_$DATE.sql.gz"
echo "==> Dumping to $OUT"
PGCLIENTENCODING=UTF8 pg_dump --no-owner --no-acl --clean --if-exists "$DB_URL" | gzip -9 > "$OUT"
echo "==> Size: $(du -h "$OUT" | cut -f1)"

if [ -n "${BACKUP_S3_TARGET:-}" ] && command -v aws >/dev/null 2>&1; then
  echo "==> Uploading to $BACKUP_S3_TARGET"
  aws s3 cp "$OUT" "$BACKUP_S3_TARGET/"
fi

# Rotate locally
find "$BACKUP_DIR" -name 'businessradar_*.sql.gz' -mtime +"$RETENTION_DAYS" -delete
echo "==> Done."
