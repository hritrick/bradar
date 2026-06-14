"""Discovery + dedup + enrich + persist pipeline."""
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, date
from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from rapidfuzz import fuzz
from models import Business, Prediction, LeadScore
from ai_service import run_full_ai_pipeline

log = logging.getLogger(__name__)


def normalize_name(n: str) -> str:
    if not n:
        return ""
    n = n.lower().strip()
    for sfx in [" pvt ltd", " private limited", " llp", " ltd", " limited", " inc", " corp", " .com", " technologies", " solutions"]:
        n = n.replace(sfx, "")
    return " ".join(n.split())


async def find_duplicate(db: AsyncSession, candidate: Dict[str, Any]) -> Business | None:
    """Find existing business that likely matches candidate by name+pincode and phone/email."""
    name = candidate.get("business_name") or ""
    norm = normalize_name(name)
    pincode = (candidate.get("pincode") or "").strip()
    phone = (candidate.get("phone") or "").strip()
    email = (candidate.get("email") or "").strip().lower()
    if not norm:
        return None
    # Pull candidates by exact phone/email OR by pincode neighborhood
    stmt = select(Business)
    cond = []
    if phone:
        cond.append(Business.phone == phone)
    if email:
        cond.append(func.lower(Business.email) == email)
    if pincode:
        cond.append(Business.pincode == pincode)
    if not cond:
        return None
    stmt = stmt.where(or_(*cond)).limit(50)
    res = await db.execute(stmt)
    for existing in res.scalars():
        existing_norm = normalize_name(existing.business_name or "")
        score = fuzz.token_set_ratio(norm, existing_norm)
        if existing.phone and existing.phone == phone and phone:
            return existing
        if existing.email and email and existing.email.lower() == email:
            return existing
        if score >= 88 and existing.pincode == pincode and pincode:
            return existing
    return None


async def ingest_business(
    db: AsyncSession,
    candidate: Dict[str, Any],
    *,
    run_ai: bool = True,
) -> Tuple[Business, bool]:
    """Insert or update a business; returns (business, created). Runs AI enrich/predict/score if run_ai."""
    dup = await find_duplicate(db, candidate)
    created = False
    if dup:
        biz = dup
        # update missing fields only
        for k, v in candidate.items():
            if v in (None, "", []) :
                continue
            if hasattr(biz, k) and getattr(biz, k) in (None, "", 0):
                setattr(biz, k, v)
        biz.updated_at = datetime.utcnow()
    else:
        # parse date if string
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
        snapshot = {
            "business_name": biz.business_name,
            "city": biz.city,
            "state": biz.state,
            "pincode": biz.pincode,
            "company_type": biz.company_type,
            "category": biz.category,
            "website": biz.website,
            "phone": biz.phone,
            "email": biz.email,
            "registration_date": str(biz.registration_date) if biz.registration_date else None,
            "employee_estimate": biz.employee_estimate,
        }
        ai = await run_full_ai_pipeline(snapshot)
        if ai["enrich"]:
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
            cat = sc.get("lead_category")
            if not cat:
                cat = "HOT" if score_int >= 75 else "WARM" if score_int >= 50 else "COLD"
            db.add(LeadScore(
                business_id=biz.id,
                score=score_int,
                lead_category=cat,
                scoring_reason=sc.get("scoring_reason"),
            ))
    await db.commit()
    await db.refresh(biz)
    return biz, created
