"""Businesses routes (list, get, create, update, delete, enrich, upload-csv)."""
import csv
import io
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Request
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


def _apply_filters(stmt, *, search, city, state, industry, category, pincode, source,
                   registered_after, registered_before):
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(or_(
            func.lower(Business.business_name).like(like),
            func.lower(Business.director_name).like(like),
            func.lower(Business.email).like(like),
            func.lower(Business.phone).like(like),
            func.lower(Business.gst_number).like(like),
        ))
    if city:
        stmt = stmt.where(Business.city.in_(city))
    if state:
        stmt = stmt.where(Business.state.in_(state))
    if industry:
        stmt = stmt.where(Business.industry.in_(industry))
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
    industry: Optional[List[str]] = Query(None),
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

    # Latest score subquery
    latest_q = (
        select(LeadScore.business_id, func.max(LeadScore.created_at).label("mx"))
        .group_by(LeadScore.business_id)
        .subquery()
    )
    latest_ls = (
        select(LeadScore.business_id, LeadScore.score, LeadScore.lead_category)
        .join(latest_q, and_(LeadScore.business_id == latest_q.c.business_id, LeadScore.created_at == latest_q.c.mx))
    ).subquery()
    latest_pq = (
        select(Prediction.business_id, func.max(Prediction.created_at).label("mx"))
        .group_by(Prediction.business_id)
        .subquery()
    )
    latest_pred = (
        select(Prediction.business_id, Prediction.predicted_need)
        .join(latest_pq, and_(Prediction.business_id == latest_pq.c.business_id, Prediction.created_at == latest_pq.c.mx))
    ).subquery()

    base = select(
        Business,
        latest_ls.c.score,
        latest_ls.c.lead_category,
        latest_pred.c.predicted_need,
    ).outerjoin(latest_ls, latest_ls.c.business_id == Business.id) \
     .outerjoin(latest_pred, latest_pred.c.business_id == Business.id)

    base = _apply_filters(base, search=search, city=city, state=state, industry=industry, category=category,
                          pincode=pincode, source=source,
                          registered_after=registered_after, registered_before=registered_before)
    if min_score is not None:
        base = base.where(latest_ls.c.score >= min_score)
    if max_score is not None:
        base = base.where(latest_ls.c.score <= max_score)
    if lead_category:
        base = base.where(latest_ls.c.lead_category.in_(lead_category))
    if predicted_need:
        base = base.where(latest_pred.c.predicted_need.in_(predicted_need))

    sort_col_name = sort.lstrip("-")
    sort_col = getattr(Business, sort_col_name, Business.created_at)
    sort_fn = desc if sort.startswith("-") else asc
    base = base.order_by(sort_fn(sort_col))

    # Count via subquery on the filtered query
    count_stmt = select(func.count()).select_from(base.order_by(None).subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * page_size
    res = await db.execute(base.offset(offset).limit(page_size))

    items = []
    for row in res.all():
        b: Business = row[0]
        score, lead_cat, pred_need = row[1], row[2], row[3]
        items.append(BusinessListItem(
            id=b.id, business_name=b.business_name, gst_number=b.gst_number, city=b.city, state=b.state,
            industry=b.industry, category=b.category, sub_category=b.sub_category,
            registration_date=b.registration_date, pincode=b.pincode,
            director_name=b.director_name, phone=b.phone, email=b.email,
            source=b.source, enrichment_status=b.enrichment_status,
            confidence_score=b.confidence_score,
            latest_score=score, latest_lead_category=lead_cat, latest_predicted_need=pred_need,
            created_at=b.created_at,
        ))
    return BusinessListResponse(total=int(total), page=page, page_size=page_size, items=items)


@router.get("/distinct")
async def get_distinct_values(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    cities = [r[0] for r in (await db.execute(select(Business.city).where(Business.city.isnot(None)).distinct())).all()]
    states = [r[0] for r in (await db.execute(select(Business.state).where(Business.state.isnot(None)).distinct())).all()]
    industries = [r[0] for r in (await db.execute(select(Business.industry).where(Business.industry.isnot(None)).distinct())).all()]
    categories = [r[0] for r in (await db.execute(select(Business.category).where(Business.category.isnot(None)).distinct())).all()]
    sources = [r[0] for r in (await db.execute(select(Business.source).where(Business.source.isnot(None)).distinct())).all()]
    preds = [r[0] for r in (await db.execute(select(Prediction.predicted_need).where(Prediction.predicted_need.isnot(None)).distinct())).all()]
    return {
        "cities": sorted(filter(None, cities)),
        "states": sorted(filter(None, states)),
        "industries": sorted(filter(None, industries)),
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
async def create_business(body: BusinessCreate, request: Request,
                           db: AsyncSession = Depends(get_db), me: User = Depends(ANALYST_OR_ADMIN)):
    payload = body.model_dump()
    payload["source"] = payload.get("source") or "manual"
    biz, created = await ingest_business(db, payload, run_ai=True)
    await write_audit(db, user_id=me.id, user_email=me.email,
                      action="create_business" if created else "update_business",
                      entity_type="business", entity_id=biz.id,
                      after_value={"business_name": biz.business_name, "city": biz.city, "industry": biz.industry},
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
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
    payload = {
        "business_name": b.business_name, "city": b.city, "state": b.state, "pincode": b.pincode,
        "company_type": b.company_type, "category": b.category, "industry": b.industry,
        "website": b.website, "phone": b.phone, "email": b.email, "gst_number": b.gst_number,
        "registration_date": b.registration_date,
        "employee_estimate": b.employee_estimate,
    }
    biz, _ = await ingest_business(db, payload, run_ai=True)
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
            r["source"] = r.get("source") or "csv_import"
            biz, created = await ingest_business(db, r, run_ai=False, queue_for_enrichment=True)
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
