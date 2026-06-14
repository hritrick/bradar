# Business Radar AI — Backup & Restore Runbook

## What's backed up
- The PostgreSQL database `businessradar_db` (entire schema + data).
- The settings table includes encrypted-at-rest secrets; rotate them after restore in non-prod.

## Daily backup (preview / staging)

A shell script ships at `/app/backend/scripts/backup_db.sh`. To enable a daily cron in this
environment, add a supervisor entry **OR** run the script via the host's crontab.

Example supervisor stanza:
```ini
[program:db-backup]
command=/app/backend/scripts/backup_db.sh
autorestart=false
startsecs=0
; Run daily via supervisor + a wrapper, or prefer host-level cron / Kubernetes CronJob.
```

Production recommendation: use Kubernetes CronJob (separate from the app pod) or your managed-DB
provider's native scheduled snapshots (RDS / Cloud SQL / Supabase).

## Retention
Default local retention: **14 days** (`BACKUP_RETENTION_DAYS`). For production, prefer object
storage versioning + lifecycle policy (7d hot, 30d warm, 1y cold).

## Off-site upload (optional)
Set `BACKUP_S3_TARGET=s3://<bucket>/<prefix>` and ensure `aws` CLI is configured with credentials.
The script will upload after dumping locally.

## Restore
```bash
# 1. Stop the app to prevent partial writes
supervisorctl stop backend

# 2. Drop existing data (DESTRUCTIVE!)
psql "$DATABASE_URL_SYNC" -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'

# 3. Restore
gunzip -c /app/backend/backups/businessradar_<TIMESTAMP>.sql.gz | psql "$DATABASE_URL_SYNC"

# 4. Restart the app (Alembic will be a no-op if schema is current)
supervisorctl start backend
```

## Recovery Point / Recovery Time Objectives
- **RPO** (data loss tolerance): ≤ 24h with daily dumps. Tighten to ≤ 15min with WAL-G / managed PITR.
- **RTO** (downtime tolerance): ≤ 15min for a ~10GB dump on commodity hardware.

## Verification
After restore, verify:
```bash
psql "$DATABASE_URL_SYNC" -c 'SELECT count(*) FROM businesses;'
psql "$DATABASE_URL_SYNC" -c "SELECT version_num FROM alembic_version;"
```

## Moving the DB outside the app pod (production)
1. Provision a managed Postgres instance (AWS RDS / GCP Cloud SQL / Supabase / Crunchy).
2. Configure VPC peering / private networking so the app pod can reach it on 5432.
3. Update `DATABASE_URL` and `DATABASE_URL_SYNC` in the app's secret store (NOT in `.env`).
4. Restart the app. Alembic will run `upgrade head` against the new instance.
5. Decommission the in-pod Postgres (`supervisorctl remove postgresql`) and delete its data dir.
6. Configure backups on the managed provider (point-in-time recovery is ideal).

The application already reads the DB URL from env so no code change is needed.
