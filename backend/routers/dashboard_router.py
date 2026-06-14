"""Dashboard analytics route — SQL aggregation (10k+ records ready)."""
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import Business, Prediction, LeadScore, User
from deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


async def _latest_lead_scores_subq(db: AsyncSession):
    # latest LeadScore per business via window-free approach: group by business_id with max(created_at)
    latest_q = (
        select(LeadScore.business_id, func.max(LeadScore.created_at).label("mx"))
        .group_by(LeadScore.business_id)
        .subquery()
    )
    return latest_q


@router.get("")
async def get_dashboard(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    today = date.today()
    day_start = datetime.combine(today, datetime.min.time())
    day_end = day_start + timedelta(days=1)

    total = (await db.execute(select(func.count(Business.id)))).scalar() or 0
    today_count = (await db.execute(
        select(func.count(Business.id)).where(Business.created_at >= day_start, Business.created_at < day_end)
    )).scalar() or 0

    # 7-day trend
    seven_days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        ds = datetime.combine(d, datetime.min.time())
        de = ds + timedelta(days=1)
        cnt = (await db.execute(
            select(func.count(Business.id)).where(Business.created_at >= ds, Business.created_at < de)
        )).scalar() or 0
        seven_days.append({"date": d.isoformat(), "count": cnt})

    # Latest lead-scores per business (SQL)
    latest = await _latest_lead_scores_subq(db)
    latest_join = (
        select(LeadScore.business_id, LeadScore.score, LeadScore.lead_category)
        .join(latest, and_(LeadScore.business_id == latest.c.business_id, LeadScore.created_at == latest.c.mx))
    ).subquery()

    cat_counts = (await db.execute(
        select(latest_join.c.lead_category, func.count()).group_by(latest_join.c.lead_category)
    )).all()
    by_cat = {r[0]: r[1] for r in cat_counts}
    hot = int(by_cat.get("HOT") or 0)
    warm = int(by_cat.get("WARM") or 0)
    cold = int(by_cat.get("COLD") or 0)
    avg_score = float((await db.execute(select(func.avg(latest_join.c.score)))).scalar() or 0)

    by_city_rows = (await db.execute(
        select(Business.city, func.count(Business.id)).where(Business.city.isnot(None)).group_by(Business.city).order_by(func.count(Business.id).desc()).limit(8)
    )).all()
    by_city = [{"city": r[0], "count": r[1]} for r in by_city_rows]

    by_industry_rows = (await db.execute(
        select(Business.industry, func.count(Business.id)).where(Business.industry.isnot(None)).group_by(Business.industry).order_by(func.count(Business.id).desc()).limit(8)
    )).all()
    by_industry = [{"industry": r[0], "count": r[1]} for r in by_industry_rows]

    by_cat_rows = (await db.execute(
        select(Business.category, func.count(Business.id)).where(Business.category.isnot(None)).group_by(Business.category).order_by(func.count(Business.id).desc()).limit(8)
    )).all()
    by_category = [{"category": r[0], "count": r[1]} for r in by_cat_rows]

    pred_rows = (await db.execute(
        select(Prediction.predicted_need, func.count(Prediction.id)).where(Prediction.predicted_need.isnot(None)).group_by(Prediction.predicted_need).order_by(func.count(Prediction.id).desc()).limit(8)
    )).all()
    by_need = [{"need": r[0], "count": r[1]} for r in pred_rows]

    # Pincode hot leads (geo)
    pin_rows = (await db.execute(
        select(Business.pincode, func.count(Business.id))
        .where(Business.pincode.isnot(None))
        .group_by(Business.pincode)
        .order_by(func.count(Business.id).desc())
        .limit(10)
    )).all()
    by_pincode = [{"pincode": r[0], "count": r[1]} for r in pin_rows]

    # Recent discoveries (latest 10)
    recent_rows = (await db.execute(
        select(Business).order_by(Business.created_at.desc()).limit(10)
    )).scalars().all()
    # Pre-fetch their latest score
    biz_ids = [b.id for b in recent_rows]
    score_map = {}
    if biz_ids:
        ls_rows = (await db.execute(select(latest_join).where(latest_join.c.business_id.in_(biz_ids)))).all()
        score_map = {r[0]: {"score": r[1], "lead_category": r[2]} for r in ls_rows}
    recent = []
    for b in recent_rows:
        ls = score_map.get(b.id) or {}
        recent.append({
            "id": b.id,
            "business_name": b.business_name,
            "city": b.city,
            "industry": b.industry,
            "category": b.category,
            "created_at": b.created_at.isoformat(),
            "score": ls.get("score"),
            "lead_category": ls.get("lead_category"),
        })

    return {
        "kpis": {
            "total_businesses": int(total),
            "today_new": int(today_count),
            "hot_leads": hot,
            "warm_leads": warm,
            "cold_leads": cold,
            "avg_score": round(avg_score, 1),
        },
        "seven_days": seven_days,
        "by_city": by_city,
        "by_industry": by_industry,
        "by_category": by_category,
        "by_predicted_need": by_need,
        "by_pincode": by_pincode,
        "recent": recent,
    }
