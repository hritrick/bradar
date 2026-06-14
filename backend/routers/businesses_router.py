"""Businesses routes (list, get, create, update, delete, enrich, upload-csv)."""
import csv
import io
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database import get_db
from models import Business, Prediction, LeadScore, User
from schemas import (
    BusinessCreate, BusinessUpdate, BusinessOut, BusinessListResponse, BusinessListItem,
)
from deps import get_current_user, require_roles
from audit import write_audit
from pipeline import ingest_business
from reports_service import fetch_businesses_for_export, businesses_to_csv, businesses_to_xlsx

router = APIRouter(prefix="/businesses", tags=["businesses"])
ANALYST_OR_ADMIN = require_roles(["Admin", "Analyst"])


def _apply_filters(stmt, *, search, city, state, category, pincode, source,
                   registered_after, registered_before):
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(or_(
            func.lower(Business.business_name).like(like),
            func.lower(Business.director_name).like(like),
            func.lower(Business.email).like(like),
            func.lower(Business.phone).like(like),
        ))
    if city:
        stmt = stmt.where(Business.city.in_(city))
    if state:
        stmt = stmt.where(Business.state.in_(state))
    if category:
        stmt = stmt.where(Business.category.in_(category))
    if pincode:
        stmt = stmt.where(Business.pincode == pincode)
    if source:
        stmt = stmt.where(Business.source.in_(source))
    if registered_after:
        stmt = stmt.where(Business.registration_date >= registered_after)
    if registered_before:
        stmt = stmt.where(Business.registration_date <= registered_before)
    return stmt


@router.get("", response_model=BusinessListResponse)
async def list_businesses(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    search: Optional[str] = None,
    city: Optional[List[str]] = Query(None),
    state: Optional[List[str]] = Query(None),
    category: Optional[List[str]] = Query(None),
    pincode: Optional[str] = None,
    source: Optional[List[str]] = Query(None),
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    lead_category: Optional[List[str]] = Query(None),
    predicted_need: Optional[List[str]] = Query(None),
    registered_after: Optional[date] = None,
    registered_before: Optional[date] = None,
    page: int = 1,
    page_size: int = 25,
    sort: str = "-created_at",
):
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    base = select(Business)
    base = _apply_filters(base, search=search, city=city, state=state, category=category,
                          pincode=pincode, source=source,
                          registered_after=registered_after, registered_before=registered_before)

    # Sort
    sort_col_name = sort.lstrip("-")
    sort_col = getattr(Business, sort_col_name, Business.created_at)
    sort_fn = desc if sort.startswith("-") else asc
    base = base.order_by(sort_fn(sort_col))

    # Count
    count_stmt = select(func.count()).select_from(base.order_by(None).subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    res = await db.execute(base.offset(offset).limit(page_size))
    rows = res.scalars().all()
    biz_ids = [b.id for b in rows]

    latest_score = {}
    latest_pred = {}
    if biz_ids:
        ls_res = await db.execute(select(LeadScore).where(LeadScore.business_id.in_(biz_ids)))
        for ls in ls_res.scalars():
            cur = latest_score.get(ls.business_id)
            if not cur or (ls.created_at and (not cur.created_at or ls.created_at > cur.created_at)):
                latest_score[ls.business_id] = ls
        pr_res = await db.execute(select(Prediction).where(Prediction.business_id.in_(biz_ids)))
        for pr in pr_res.scalars():
            cur = latest_pred.get(pr.business_id)
            if not cur or (pr.created_at and (not cur.created_at or pr.created_at > cur.created_at)):
                latest_pred[pr.business_id] = pr

    # Optional post-filter for score/lead/predicted_need
    items = []
    for b in rows:
        ls = latest_score.get(b.id)
        pr = latest_pred.get(b.id)
        if min_score is not None and (ls is None or (ls.score or 0) < min_score):
            continue
        if max_score is not None and (ls is None or (ls.score or 0) > max_score):
            continue
        if lead_category and (ls is None or ls.lead_category not in lead_category):
            continue
        if predicted_need and (pr is None or pr.predicted_need not in predicted_need):
            continue
        items.append(BusinessListItem(
            id=b.id, business_name=b.business_name, city=b.city, state=b.state,
            category=b.category, sub_category=b.sub_category, registration_date=b.registration_date,
            pincode=b.pincode, director_name=b.director_name, phone=b.phone, email=b.email,
            source=b.source, enrichment_status=b.enrichment_status,
            confidence_score=b.confidence_score,
            latest_score=ls.score if ls else None,
            latest_lead_category=ls.lead_category if ls else None,
            latest_predicted_need=pr.predicted_need if pr else None,
            created_at=b.created_at,
        ))
    return BusinessListResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/distinct")
async def get_distinct_values(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    cities = [r[0] for r in (await db.execute(select(Business.city).where(Business.city.isnot(None)).distinct())).all()]
    states = [r[0] for r in (await db.execute(select(Business.state).where(Business.state.isnot(None)).distinct())).all()]
    categories = [r[0] for r in (await db.execute(select(Business.category).where(Business.category.isnot(None)).distinct())).all()]
    sources = [r[0] for r in (await db.execute(select(Business.source).where(Business.source.isnot(None)).distinct())).all()]
    preds = [r[0] for r in (await db.execute(select(Prediction.predicted_need).where(Prediction.predicted_need.isnot(None)).distinct())).all()]
    return {
        "cities": sorted(filter(None, cities)),
        "states": sorted(filter(None, states)),
        "categories": sorted(filter(None, categories)),
        "sources": sorted(filter(None, sources)),
        "predicted_needs": sorted(filter(None, preds)),
    }


@router.get("/{business_id}", response_model=BusinessOut)
async def get_business(business_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    res = await db.execute(
        select(Business)
        .options(selectinload(Business.predictions), selectinload(Business.lead_scores))
        .where(Business.id == business_id)
    )
    b = res.scalar_one_or_none()
    if not b:
        raise HTTPException(404, "Business not found")
    return BusinessOut.model_validate(b)


@router.post("", response_model=BusinessOut, status_code=201)
async def create_business(body: BusinessCreate, request: Request, background: BackgroundTasks,
                           db: AsyncSession = Depends(get_db), me: User = Depends(ANALYST_OR_ADMIN)):
    payload = body.model_dump()
    payload["source"] = payload.get("source") or "manual"
    biz, created = await ingest_business(db, payload, run_ai=True)
    await write_audit(db, user_id=me.id, user_email=me.email, action="create_business" if created else "update_business",
                      entity_type="business", entity_id=biz.id, after_value={"business_name": biz.business_name, "city": biz.city},
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
    # reload with relationships
    res = await db.execute(select(Business).options(selectinload(Business.predictions), selectinload(Business.lead_scores)).where(Business.id == biz.id))
    return BusinessOut.model_validate(res.scalar_one())


@router.patch("/{business_id}", response_model=BusinessOut)
async def update_business(business_id: str, body: BusinessUpdate, request: Request,
                          db: AsyncSession = Depends(get_db), me: User = Depends(ANALYST_OR_ADMIN)):
    res = await db.execute(select(Business).where(Business.id == business_id))
    b = res.scalar_one_or_none()
    if not b:
        raise HTTPException(404, "Business not found")
    before = {"name": b.business_name, "city": b.city}
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(b, k, v)
    await db.commit()
    res = await db.execute(select(Business).options(selectinload(Business.predictions), selectinload(Business.lead_scores)).where(Business.id == business_id))
    b = res.scalar_one()
    await write_audit(db, user_id=me.id, user_email=me.email, action="update_business",
                      entity_type="business", entity_id=b.id, before_value=before,
                      after_value={"name": b.business_name, "city": b.city},
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
    return BusinessOut.model_validate(b)


@router.delete("/{business_id}", status_code=204)
async def delete_business(business_id: str, request: Request, db: AsyncSession = Depends(get_db), me: User = Depends(require_roles(["Admin"]))):
    res = await db.execute(select(Business).where(Business.id == business_id))
    b = res.scalar_one_or_none()
    if not b:
        raise HTTPException(404, "Business not found")
    name = b.business_name
    await db.delete(b)
    await db.commit()
    await write_audit(db, user_id=me.id, user_email=me.email, action="delete_business", entity_type="business", entity_id=business_id,
                      before_value={"name": name},
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))


@router.post("/{business_id}/enrich", response_model=BusinessOut)
async def rerun_ai(business_id: str, request: Request, db: AsyncSession = Depends(get_db), me: User = Depends(ANALYST_OR_ADMIN)):
    res = await db.execute(select(Business).where(Business.id == business_id))
    b = res.scalar_one_or_none()
    if not b:
        raise HTTPException(404, "Business not found")
    snapshot = {
        "business_name": b.business_name,
        "city": b.city,
        "state": b.state,
        "pincode": b.pincode,
        "company_type": b.company_type,
        "category": b.category,
        "website": b.website,
        "registration_date": str(b.registration_date) if b.registration_date else None,
        "employee_estimate": b.employee_estimate,
    }
    biz, _ = await ingest_business(db, snapshot | {"business_name": b.business_name, "id": b.id}, run_ai=True)
    await write_audit(db, user_id=me.id, user_email=me.email, action="rerun_ai", entity_type="business", entity_id=biz.id,
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
    res = await db.execute(select(Business).options(selectinload(Business.predictions), selectinload(Business.lead_scores)).where(Business.id == biz.id))
    return BusinessOut.model_validate(res.scalar_one())


@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), preview: bool = True, request: Request = None,
                    db: AsyncSession = Depends(get_db), me: User = Depends(ANALYST_OR_ADMIN)):
    raw = (await file.read()).decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(raw))
    rows = []
    for row in reader:
        rows.append({k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()})
    if preview:
        return {"preview": True, "row_count": len(rows), "sample": rows[:5]}
    inserted = 0
    duplicates = 0
    errors = []
    for r in rows:
        try:
            if not r.get("business_name"):
                continue
            r["source"] = r.get("source") or "csv_upload"
            biz, created = await ingest_business(db, r, run_ai=False)
            if created:
                inserted += 1
            else:
                duplicates += 1
        except Exception as e:
            errors.append(str(e)[:200])
    await write_audit(db, user_id=me.id, user_email=me.email, action="csv_upload", entity_type="business",
                      after_value={"file": file.filename, "rows": len(rows), "inserted": inserted, "duplicates": duplicates},
                      ip_address=request.client.host if request and request.client else None,
                      user_agent=request.headers.get("user-agent") if request else None)
    return {"preview": False, "row_count": len(rows), "inserted": inserted, "duplicates": duplicates, "errors": errors}


@router.get("/export/csv")
async def export_csv(ids: Optional[str] = None, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    id_list = ids.split(",") if ids else None
    rows = await fetch_businesses_for_export(db, ids=id_list)
    data = businesses_to_csv(rows)
    return StreamingResponse(io.BytesIO(data), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=businesses.csv"})


@router.get("/export/xlsx")
async def export_xlsx(ids: Optional[str] = None, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    id_list = ids.split(",") if ids else None
    rows = await fetch_businesses_for_export(db, ids=id_list)
    data = businesses_to_xlsx(rows)
    return StreamingResponse(io.BytesIO(data),
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=businesses.xlsx"})
