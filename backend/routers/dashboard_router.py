"""Dashboard analytics route."""
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import Business, Prediction, LeadScore, User
from deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    today = date.today()
    day_start = datetime.combine(today, datetime.min.time())
    day_end = day_start + timedelta(days=1)

    total = (await db.execute(select(func.count(Business.id)))).scalar() or 0
    today_count = (await db.execute(select(func.count(Business.id)).where(Business.created_at >= day_start, Business.created_at < day_end))).scalar() or 0

    # Past 7 days new-business trend
    seven_days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        ds = datetime.combine(d, datetime.min.time())
        de = ds + timedelta(days=1)
        cnt = (await db.execute(select(func.count(Business.id)).where(Business.created_at >= ds, Business.created_at < de))).scalar() or 0
        seven_days.append({"date": d.isoformat(), "count": cnt})

    # Latest score by biz (in python, MVP)
    ls_res = await db.execute(select(LeadScore))
    by_biz = {}
    for ls in ls_res.scalars():
        cur = by_biz.get(ls.business_id)
        if not cur or (ls.created_at and (not cur.created_at or ls.created_at > cur.created_at)):
            by_biz[ls.business_id] = ls
    hot = sum(1 for v in by_biz.values() if v.lead_category == "HOT")
    warm = sum(1 for v in by_biz.values() if v.lead_category == "WARM")
    cold = sum(1 for v in by_biz.values() if v.lead_category == "COLD")
    avg_score = round((sum((v.score or 0) for v in by_biz.values()) / len(by_biz)), 1) if by_biz else 0

    by_city_res = await db.execute(
        select(Business.city, func.count(Business.id)).where(Business.city.isnot(None)).group_by(Business.city)
    )
    by_city = sorted([{"city": r[0], "count": r[1]} for r in by_city_res.all()], key=lambda x: -x["count"])[:8]
    by_cat_res = await db.execute(
        select(Business.category, func.count(Business.id)).where(Business.category.isnot(None)).group_by(Business.category)
    )
    by_category = sorted([{"category": r[0], "count": r[1]} for r in by_cat_res.all()], key=lambda x: -x["count"])[:8]
    pred_res = await db.execute(
        select(Prediction.predicted_need, func.count(Prediction.id)).where(Prediction.predicted_need.isnot(None)).group_by(Prediction.predicted_need)
    )
    by_need = sorted([{"need": r[0], "count": r[1]} for r in pred_res.all()], key=lambda x: -x["count"])[:8]

    # Recent discoveries (top 10)
    recent_res = await db.execute(select(Business).order_by(Business.created_at.desc()).limit(10))
    recent = []
    for b in recent_res.scalars():
        ls = by_biz.get(b.id)
        recent.append({
            "id": b.id,
            "business_name": b.business_name,
            "city": b.city,
            "category": b.category,
            "created_at": b.created_at.isoformat(),
            "score": ls.score if ls else None,
            "lead_category": ls.lead_category if ls else None,
        })

    return {
        "kpis": {
            "total_businesses": total,
            "today_new": today_count,
            "hot_leads": hot,
            "warm_leads": warm,
            "cold_leads": cold,
            "avg_score": avg_score,
        },
        "seven_days": seven_days,
        "by_city": by_city,
        "by_category": by_category,
        "by_predicted_need": by_need,
        "recent": recent,
    }
