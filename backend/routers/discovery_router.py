"""Discovery routes — provider architecture, source admin, health dashboard, run logs."""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Query, BackgroundTasks
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, SessionLocal
from models import User, DiscoverySource, DiscoverySourceRun, Business, EnrichmentQueueItem, Prediction, LeadScore
from schemas import DiscoveryRunRequest, DiscoveryRunResponse
from deps import require_roles, get_current_user
from audit import write_audit
from providers import build_providers, provider_metadata, get_provider
from pipeline import ingest_batch
import enrichment_worker

router = APIRouter(prefix="/discovery", tags=["discovery"])
log = logging.getLogger(__name__)
ANALYST_OR_ADMIN = require_roles(["Admin", "Analyst"])
ADMIN = require_roles(["Admin"])


async def _sync_source_records(db: AsyncSession) -> None:
    """Ensure a DiscoverySource row exists for each provider class."""
    metas = await provider_metadata()
    existing = {r.name: r for r in (await db.execute(select(DiscoverySource))).scalars().all()}
    changed = False
    for m in metas:
        if m["name"] in existing:
            r = existing[m["name"]]
            # keep enable/schedule but refresh display fields
            if r.display_name != m["display_name"] or r.description != m["description"]:
                r.display_name = m["display_name"]
                r.description = m["description"]
                changed = True
            r.requires_config = m["requires_config"]
        else:
            db.add(DiscoverySource(
                name=m["name"],
                display_name=m["display_name"],
                description=m["description"],
                requires_config=m["requires_config"],
                enabled=(m["name"] in ("manual", "csv_import", "synthetic")),  # safe defaults
            ))
            changed = True
    if changed:
        await db.commit()


@router.get("/connectors")
async def list_connectors_legacy(_: User = Depends(get_current_user)):
    """Backward-compatible alias for /discovery/sources."""
    return await provider_metadata()


@router.get("/sources")
async def list_sources(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    await _sync_source_records(db)
    metas = {m["name"]: m for m in await provider_metadata()}
    rows = (await db.execute(select(DiscoverySource).order_by(DiscoverySource.display_name))).scalars().all()
    out = []
    for r in rows:
        m = metas.get(r.name, {})
        out.append({
            "id": r.id,
            "name": r.name,
            "display_name": r.display_name,
            "description": r.description,
            "enabled": r.enabled,
            "schedule_cron": r.schedule_cron,
            "requires_config": r.requires_config or [],
            "configured": m.get("configured", False),
            "supports_scheduling": m.get("supports_scheduling", False),
            "supports_run_now": m.get("supports_run_now", True),
            "documentation_url": m.get("documentation_url"),
            "last_run_at": r.last_run_at.isoformat() if r.last_run_at else None,
            "last_run_status": r.last_run_status,
            "last_run_summary": r.last_run_summary or {},
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return out


@router.patch("/sources/{source_id}")
async def update_source(source_id: str, body: Dict[str, Any], request: Request,
                       db: AsyncSession = Depends(get_db), me: User = Depends(ADMIN)):
    r = (await db.execute(select(DiscoverySource).where(DiscoverySource.id == source_id))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Source not found")
    before = {"enabled": r.enabled, "schedule_cron": r.schedule_cron}
    if "enabled" in body:
        r.enabled = bool(body["enabled"])
    if "schedule_cron" in body:
        r.schedule_cron = body["schedule_cron"] or None
    await db.commit()
    await db.refresh(r)
    await write_audit(db, user_id=me.id, user_email=me.email, action="update_discovery_source",
                      entity_type="discovery_source", entity_id=r.id, before_value=before,
                      after_value={"enabled": r.enabled, "schedule_cron": r.schedule_cron},
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
    return {"ok": True, "enabled": r.enabled, "schedule_cron": r.schedule_cron}


async def _execute_run(source_name: str, limit: int, query: Optional[Dict[str, Any]], triggered_by: str) -> Dict[str, Any]:
    """Core run: provider → normalize → validate → dedup (in-batch + DB) → ingest → queue."""
    provider = await get_provider(source_name)
    if not provider:
        return {"error": f"Unknown source: {source_name}"}

    async with SessionLocal() as db:
        await _sync_source_records(db)
        src_row = (await db.execute(select(DiscoverySource).where(DiscoverySource.name == source_name))).scalar_one_or_none()
        if not src_row or not src_row.enabled:
            return {"error": f"Source '{source_name}' is disabled by admin"}
        if not provider.configured and source_name not in ("manual", "csv_import", "synthetic"):
            return {"error": f"Source '{source_name}' is not configured"}

        run = DiscoverySourceRun(source_id=src_row.id, source_name=source_name, triggered_by=triggered_by)
        db.add(run)
        await db.commit()
        await db.refresh(run)

    try:
        raw_rows = await provider.discover_businesses(limit=limit, query=query)
        records_found = len(raw_rows)
        normalized = []
        invalid = 0
        for raw in raw_rows:
            try:
                n = provider.normalize_data(raw)
                v = provider.validate(n)
                if not v.valid:
                    invalid += 1
                    continue
                normalized.append(n)
            except Exception as e:
                invalid += 1
                log.warning(f"normalize/validate failed: {e}")

        # Dedup via provider's deduplicate method (uses our find_duplicate_v2)
        async def find_dup_db(c):
            from pipeline import find_duplicate_v2
            async with SessionLocal() as db2:
                return await find_duplicate_v2(db2, c)
        unique, batch_dups = await provider.deduplicate(normalized, find_dup_db)

        # Ingest in one transaction
        async with SessionLocal() as db:
            counts = await ingest_batch(db, unique, run_ai=False, queue_for_enrichment=True)

        async with SessionLocal() as db:
            r = (await db.execute(select(DiscoverySourceRun).where(DiscoverySourceRun.id == run.id))).scalar_one()
            r.records_found = records_found
            r.invalid_records = invalid
            r.duplicates_removed = len(batch_dups) + counts["duplicates"]
            r.records_added = counts["inserted"]
            r.enrichment_queued = counts["enrichment_queued"]
            r.status = "success"
            r.finished_at = datetime.utcnow()
            r.message = f"OK — added {counts['inserted']}, dups {r.duplicates_removed}, invalid {invalid}."
            # Update source row last-run
            src = (await db.execute(select(DiscoverySource).where(DiscoverySource.id == r.source_id))).scalar_one()
            src.last_run_at = r.finished_at
            src.last_run_status = r.status
            src.last_run_summary = {
                "records_found": r.records_found,
                "records_added": r.records_added,
                "duplicates_removed": r.duplicates_removed,
                "errors_count": r.errors_count,
                "enrichment_queued": r.enrichment_queued,
            }
            await db.commit()
        return {
            "source": source_name,
            "records_found": records_found,
            "records_added": counts["inserted"],
            "duplicates_removed": (len(batch_dups) + counts["duplicates"]),
            "invalid_records": invalid,
            "enrichment_queued": counts["enrichment_queued"],
            "errors": [],
        }
    except Exception as e:
        log.exception("Discovery run failed")
        async with SessionLocal() as db:
            r = (await db.execute(select(DiscoverySourceRun).where(DiscoverySourceRun.id == run.id))).scalar_one()
            r.status = "failed"
            r.errors_count = 1
            r.errors = [str(e)[:300]]
            r.finished_at = datetime.utcnow()
            r.message = str(e)[:300]
            await db.commit()
        return {"source": source_name, "records_found": 0, "records_added": 0, "duplicates_removed": 0, "invalid_records": 0, "enrichment_queued": 0, "errors": [str(e)[:300]]}


@router.post("/run", response_model=DiscoveryRunResponse)
async def run_discovery_legacy(body: DiscoveryRunRequest, request: Request, me: User = Depends(ANALYST_OR_ADMIN)):
    res = await _execute_run(body.source, body.limit, body.query, triggered_by=me.email)
    async with SessionLocal() as db:
        await write_audit(db, user_id=me.id, user_email=me.email, action="discovery_run",
                          entity_type="discovery", entity_id=body.source,
                          after_value=res,
                          ip_address=request.client.host if request.client else None,
                          user_agent=request.headers.get("user-agent"))
    if "error" in res:
        raise HTTPException(400, res["error"])
    return DiscoveryRunResponse(
        source=res["source"],
        fetched=res["records_found"],
        inserted=res["records_added"],
        duplicates=res["duplicates_removed"],
        enriched=res["enrichment_queued"],
        errors=res["errors"],
    )


@router.post("/sources/{source_id}/run")
async def run_now(source_id: str, body: Optional[Dict[str, Any]] = None, request: Request = None,
                 me: User = Depends(ANALYST_OR_ADMIN)):
    async with SessionLocal() as db:
        src = (await db.execute(select(DiscoverySource).where(DiscoverySource.id == source_id))).scalar_one_or_none()
        if not src:
            raise HTTPException(404, "Source not found")
    limit = (body or {}).get("limit", 20)
    query = (body or {}).get("query")
    res = await _execute_run(src.name, limit, query, triggered_by=me.email)
    async with SessionLocal() as db:
        await write_audit(db, user_id=me.id, user_email=me.email, action="discovery_run",
                          entity_type="discovery_source", entity_id=src.id,
                          after_value=res,
                          ip_address=request.client.host if request and request.client else None,
                          user_agent=request.headers.get("user-agent") if request else None)
    if "error" in res:
        raise HTTPException(400, res["error"])
    return res


@router.get("/sources/{source_id}/runs")
async def source_runs(source_id: str, limit: int = 50,
                     db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    src = (await db.execute(select(DiscoverySource).where(DiscoverySource.id == source_id))).scalar_one_or_none()
    if not src:
        raise HTTPException(404, "Source not found")
    runs = (await db.execute(
        select(DiscoverySourceRun).where(DiscoverySourceRun.source_id == source_id)
        .order_by(desc(DiscoverySourceRun.started_at)).limit(min(200, max(1, limit)))
    )).scalars().all()
    return [
        {
            "id": r.id, "status": r.status, "triggered_by": r.triggered_by,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "records_found": r.records_found, "records_added": r.records_added,
            "duplicates_removed": r.duplicates_removed, "invalid_records": r.invalid_records,
            "errors_count": r.errors_count, "errors": r.errors or [],
            "enrichment_queued": r.enrichment_queued,
            "message": r.message,
        }
        for r in runs
    ]


@router.get("/health")
async def source_health(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    await _sync_source_records(db)
    metas = {m["name"]: m for m in await provider_metadata()}
    srcs = (await db.execute(select(DiscoverySource).order_by(DiscoverySource.display_name))).scalars().all()
    # Aggregate per source
    per_source = []
    total_added = total_found = total_dups = total_errors = 0
    for s in srcs:
        agg = (await db.execute(
            select(
                func.coalesce(func.sum(DiscoverySourceRun.records_found), 0),
                func.coalesce(func.sum(DiscoverySourceRun.records_added), 0),
                func.coalesce(func.sum(DiscoverySourceRun.duplicates_removed), 0),
                func.coalesce(func.sum(DiscoverySourceRun.errors_count), 0),
                func.count(DiscoverySourceRun.id),
            ).where(DiscoverySourceRun.source_id == s.id)
        )).first()
        found, added, dups, errs, runs_count = agg
        m = metas.get(s.name, {})
        per_source.append({
            "id": s.id,
            "name": s.name,
            "display_name": s.display_name,
            "enabled": s.enabled,
            "configured": m.get("configured", False),
            "requires_config": s.requires_config or [],
            "schedule_cron": s.schedule_cron,
            "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
            "last_run_status": s.last_run_status,
            "records_found": int(found or 0),
            "records_added": int(added or 0),
            "duplicates_removed": int(dups or 0),
            "errors": int(errs or 0),
            "runs": int(runs_count or 0),
        })
        total_found += int(found or 0)
        total_added += int(added or 0)
        total_dups += int(dups or 0)
        total_errors += int(errs or 0)
    # Enrichment queue status
    q = await enrichment_worker.queue_size()
    return {
        "totals": {
            "records_found": total_found,
            "records_added": total_added,
            "duplicates_removed": total_dups,
            "errors": total_errors,
            "sources_enabled": sum(1 for s in srcs if s.enabled),
            "sources_total": len(srcs),
        },
        "queue": q,
        "sources": per_source,
    }


@router.post("/queue/process")
async def queue_process(batch: int = Query(5, ge=1, le=20), me: User = Depends(ADMIN)):
    res = await enrichment_worker.process_batch(batch=batch)
    return res


@router.get("/queue")
async def queue_status(_: User = Depends(get_current_user)):
    return await enrichment_worker.queue_size()
