"""Background enrichment worker — polls EnrichmentQueueItem and runs AI pipeline."""
import asyncio
import logging
from datetime import datetime
from sqlalchemy import select, update
from database import SessionLocal
from models import EnrichmentQueueItem, Business, Prediction, LeadScore
from ai_service import run_full_ai_pipeline

log = logging.getLogger(__name__)

_worker_task: asyncio.Task | None = None
_stop_event: asyncio.Event | None = None
BATCH = 3
POLL_INTERVAL = 30  # seconds


async def _process_one(item_id: str) -> None:
    async with SessionLocal() as db:
        item = (await db.execute(select(EnrichmentQueueItem).where(EnrichmentQueueItem.id == item_id))).scalar_one_or_none()
        if not item:
            return
        item.status = "processing"
        item.started_at = datetime.utcnow()
        item.attempts += 1
        await db.commit()

        biz = (await db.execute(select(Business).where(Business.id == item.business_id))).scalar_one_or_none()
        if not biz:
            item.status = "failed"
            item.last_error = "business missing"
            item.finished_at = datetime.utcnow()
            await db.commit()
            return
        snapshot = {
            "business_name": biz.business_name,
            "city": biz.city,
            "state": biz.state,
            "pincode": biz.pincode,
            "company_type": biz.company_type,
            "category": biz.category,
            "industry": biz.industry,
            "website": biz.website,
            "phone": biz.phone,
            "email": biz.email,
            "registration_date": str(biz.registration_date) if biz.registration_date else None,
            "employee_estimate": biz.employee_estimate,
        }
        ai = await run_full_ai_pipeline(snapshot)
        try:
            if ai["enrich"]:
                biz.category = ai["enrich"].get("category") or biz.category
                biz.sub_category = ai["enrich"].get("sub_category") or biz.sub_category
                biz.company_type = ai["enrich"].get("company_type") or biz.company_type
                try:
                    emp = int(ai["enrich"].get("employee_estimate") or 0)
                    if emp > 0:
                        biz.employee_estimate = emp
                except Exception:
                    pass
                try:
                    cs = float(ai["enrich"].get("confidence_score") or 0)
                    if 0 <= cs <= 1:
                        biz.confidence_score = cs
                except Exception:
                    pass
                biz.enrichment_status = "enriched"
            else:
                biz.enrichment_status = "failed"
            if ai["predict"]:
                db.add(Prediction(
                    business_id=biz.id,
                    predicted_need=ai["predict"].get("predicted_need"),
                    probability=float(ai["predict"].get("probability") or 0),
                    reasoning=ai["predict"].get("reasoning"),
                    model_used="gpt-4o-mini",
                ))
            if ai["score"]:
                sc = ai["score"]
                try:
                    score_int = int(sc.get("score") or 0)
                except Exception:
                    score_int = 0
                cat = sc.get("lead_category") or ("HOT" if score_int >= 75 else "WARM" if score_int >= 50 else "COLD")
                db.add(LeadScore(
                    business_id=biz.id,
                    score=score_int,
                    lead_category=cat,
                    scoring_reason=sc.get("scoring_reason"),
                ))
            item.status = "done"
            item.last_error = None
            item.finished_at = datetime.utcnow()
            await db.commit()
        except Exception as e:
            log.warning(f"enrichment apply failed: {e}")
            item.status = "failed"
            item.last_error = str(e)[:500]
            item.finished_at = datetime.utcnow()
            await db.commit()


async def process_batch(batch: int = BATCH) -> dict:
    """Process up to `batch` items from the queue. Callable on-demand by admin."""
    async with SessionLocal() as db:
        rows = (await db.execute(
            select(EnrichmentQueueItem)
            .where(EnrichmentQueueItem.status == "queued")
            .order_by(EnrichmentQueueItem.queued_at.asc())
            .limit(batch)
        )).scalars().all()
        item_ids = [r.id for r in rows]
    done = 0
    failed = 0
    for item_id in item_ids:
        try:
            await _process_one(item_id)
            done += 1
        except Exception as e:
            log.warning(f"queue item {item_id} failed: {e}")
            failed += 1
    return {"processed": done, "failed": failed, "requested": batch}


async def _worker_loop():
    log.info("Enrichment worker started (interval=%ds, batch=%d).", POLL_INTERVAL, BATCH)
    try:
        while not (_stop_event and _stop_event.is_set()):
            try:
                # Only process a small batch automatically to avoid runaway LLM costs.
                await process_batch(batch=1)
            except Exception as e:
                log.warning(f"worker batch error: {e}")
            try:
                await asyncio.wait_for(_stop_event.wait(), timeout=POLL_INTERVAL)
            except asyncio.TimeoutError:
                pass
    except asyncio.CancelledError:
        log.info("Enrichment worker cancelled.")
    log.info("Enrichment worker stopped.")


async def start_worker():
    global _worker_task, _stop_event
    if _worker_task and not _worker_task.done():
        return
    _stop_event = asyncio.Event()
    _worker_task = asyncio.create_task(_worker_loop())


async def stop_worker():
    global _worker_task, _stop_event
    if _stop_event:
        _stop_event.set()
    if _worker_task:
        try:
            await asyncio.wait_for(_worker_task, timeout=5)
        except Exception:
            pass
    _worker_task = None
    _stop_event = None


async def queue_size() -> dict:
    from sqlalchemy import func
    async with SessionLocal() as db:
        total = (await db.execute(select(func.count(EnrichmentQueueItem.id)))).scalar() or 0
        queued = (await db.execute(select(func.count(EnrichmentQueueItem.id)).where(EnrichmentQueueItem.status == "queued"))).scalar() or 0
        processing = (await db.execute(select(func.count(EnrichmentQueueItem.id)).where(EnrichmentQueueItem.status == "processing"))).scalar() or 0
        done = (await db.execute(select(func.count(EnrichmentQueueItem.id)).where(EnrichmentQueueItem.status == "done"))).scalar() or 0
        failed = (await db.execute(select(func.count(EnrichmentQueueItem.id)).where(EnrichmentQueueItem.status == "failed"))).scalar() or 0
    return {"total": total, "queued": queued, "processing": processing, "done": done, "failed": failed}
