"""Unified discovery pipeline v2.

flow: Provider → normalize → validate → deduplicate (GST / website / phone / name+pincode) →
     enrichment queue → (background) prediction + scoring → geo intelligence → reports.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, date
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from rapidfuzz import fuzz
from models import Business, Prediction, LeadScore, EnrichmentQueueItem
from ai_service import run_full_ai_pipeline
from geo_service import enrich_geo

log = logging.getLogger(__name__)


def _norm(s: Optional[str]) -> str:
    if not s:
        return ""
    s = s.lower().strip()
    for suf in [" pvt ltd", " private limited", " llp", " ltd", " limited", " inc", " corp", " group", " holdings"]:
        s = s.replace(suf, "")
    return " ".join(s.split())


def _norm_phone(p: Optional[str]) -> str:
    return "".join(ch for ch in (p or "") if ch.isdigit())


def _norm_website(w: Optional[str]) -> str:
    if not w:
        return ""
    w = w.lower().strip().replace("https://", "").replace("http://", "").replace("www.", "")
    return w.strip("/")


async def find_duplicate_v2(db: AsyncSession, c: Dict[str, Any]) -> Optional[Business]:
    """Match by GST (exact), website (exact), phone (exact), then business_name+pincode fuzzy."""
    gst = (c.get("gst_number") or "").strip().upper()
    website = _norm_website(c.get("website"))
    phone = _norm_phone(c.get("phone"))
    name = (c.get("business_name") or "").strip()
    pincode = (c.get("pincode") or "").strip()
    norm_name = _norm(name)

    # 1) GST exact
    if gst:
        r = await db.execute(select(Business).where(Business.gst_number == gst).limit(1))
        row = r.scalar_one_or_none()
        if row:
            return row

    # 2) website exact
    if website:
        r = await db.execute(
            select(Business).where(
                func.lower(func.regexp_replace(func.coalesce(Business.website, ''), 'https?://(www\\.)?', '')) == website
            ).limit(1)
        )
        row = r.scalar_one_or_none()
        if row:
            return row

    # 3) phone exact (digits only)
    if phone:
        r = await db.execute(
            select(Business).where(
                func.regexp_replace(func.coalesce(Business.phone, ''), '[^0-9]', '', 'g') == phone
            ).limit(1)
        )
        row = r.scalar_one_or_none()
        if row:
            return row

    # 4) business name + pincode fuzzy
    if norm_name and pincode:
        r = await db.execute(
            select(Business).where(Business.pincode == pincode).limit(50)
        )
        for existing in r.scalars():
            if fuzz.token_set_ratio(norm_name, _norm(existing.business_name)) >= 90:
                return existing
    return None


async def ingest_business(
    db: AsyncSession,
    candidate: Dict[str, Any],
    *,
    run_ai: bool = True,
    queue_for_enrichment: bool = False,
) -> Tuple[Business, bool]:
    """Insert or merge a business. Optionally runs AI immediately, otherwise enqueues for background enrichment."""
    candidate = enrich_geo(candidate)
    dup = await find_duplicate_v2(db, candidate)
    created = False
    if dup:
        biz = dup
        for k, v in candidate.items():
            if v in (None, "", []):
                continue
            if hasattr(biz, k) and getattr(biz, k) in (None, "", 0):
                setattr(biz, k, v)
        biz.updated_at = datetime.utcnow()
    else:
        rd = candidate.get("registration_date")
        if isinstance(rd, str):
            try:
                candidate["registration_date"] = date.fromisoformat(rd)
            except Exception:
                candidate["registration_date"] = None
        biz = Business(**{k: v for k, v in candidate.items() if hasattr(Business, k)})
        db.add(biz)
        await db.flush()
        created = True

    if run_ai:
        snapshot = _biz_snapshot(biz)
        ai = await run_full_ai_pipeline(snapshot)
        _apply_ai(db, biz, ai)
        biz.enrichment_status = "enriched" if ai["enrich"] else "failed"
    elif queue_for_enrichment:
        # Insert queue row if not present
        if created:
            db.add(EnrichmentQueueItem(business_id=biz.id, status="queued"))
            biz.enrichment_status = "queued"

    await db.commit()
    await db.refresh(biz)
    return biz, created


def _biz_snapshot(biz: Business) -> dict:
    return {
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


def _apply_ai(db: AsyncSession, biz: Business, ai: dict) -> None:
    if ai.get("enrich"):
        biz.category = ai["enrich"].get("category") or biz.category
        biz.sub_category = ai["enrich"].get("sub_category") or biz.sub_category
        biz.company_type = ai["enrich"].get("company_type") or biz.company_type
        try:
            emp = int(ai["enrich"].get("employee_estimate") or 0)
            if emp > 0 and not biz.employee_estimate:
                biz.employee_estimate = emp
        except Exception:
            pass
        try:
            cs = float(ai["enrich"].get("confidence_score") or 0)
            if 0 <= cs <= 1:
                biz.confidence_score = cs
        except Exception:
            pass
    if ai.get("predict"):
        db.add(Prediction(
            business_id=biz.id,
            predicted_need=ai["predict"].get("predicted_need"),
            probability=float(ai["predict"].get("probability") or 0),
            reasoning=ai["predict"].get("reasoning"),
            model_used="gpt-4o-mini",
        ))
    if ai.get("score"):
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


async def ingest_batch(
    db: AsyncSession,
    candidates: List[Dict[str, Any]],
    *,
    run_ai: bool = False,
    queue_for_enrichment: bool = True,
) -> Dict[str, int]:
    """Bulk variant used by discovery runs. Returns counts."""
    inserted = 0
    duplicates = 0
    invalid = 0
    enrichment_queued = 0
    for c in candidates:
        if not c.get("business_name"):
            invalid += 1
            continue
        c = enrich_geo(c)
        dup = await find_duplicate_v2(db, c)
        if dup:
            duplicates += 1
            continue
        rd = c.get("registration_date")
        if isinstance(rd, str):
            try:
                c["registration_date"] = date.fromisoformat(rd)
            except Exception:
                c["registration_date"] = None
        biz = Business(**{k: v for k, v in c.items() if hasattr(Business, k)})
        if queue_for_enrichment:
            biz.enrichment_status = "queued"
        db.add(biz)
        await db.flush()
        if queue_for_enrichment:
            db.add(EnrichmentQueueItem(business_id=biz.id, status="queued"))
            enrichment_queued += 1
        if run_ai:
            ai = await run_full_ai_pipeline(_biz_snapshot(biz))
            _apply_ai(db, biz, ai)
            biz.enrichment_status = "enriched" if ai.get("enrich") else "failed"
        inserted += 1
    await db.commit()
    return {
        "inserted": inserted,
        "duplicates": duplicates,
        "invalid": invalid,
        "enrichment_queued": enrichment_queued,
    }
