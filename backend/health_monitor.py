"""Source health monitor — rolling success/error stats per discovery source."""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models import DiscoverySource, DiscoverySourceRun


async def health_for_source(db: AsyncSession, source_id: str, *, lookback_hours: int = 24) -> dict:
    since = datetime.utcnow() - timedelta(hours=lookback_hours)
    base = select(DiscoverySourceRun).where(
        and_(DiscoverySourceRun.source_id == source_id, DiscoverySourceRun.started_at >= since)
    )
    rows = (await db.execute(base)).scalars().all()
    total = len(rows)
    success = sum(1 for r in rows if r.status == "success")
    failed = sum(1 for r in rows if r.status == "failed")
    running = sum(1 for r in rows if r.status == "running")
    error_rate = (failed / total) if total > 0 else 0.0
    durations = [
        (r.finished_at - r.started_at).total_seconds()
        for r in rows if r.finished_at and r.started_at
    ]
    avg_duration = (sum(durations) / len(durations)) if durations else 0.0
    last_failure = max((r.started_at for r in rows if r.status == "failed"), default=None)
    last_success = max((r.started_at for r in rows if r.status == "success"), default=None)
    # Alert level:
    #   green  : 0 failures in window  OR error_rate < 5%
    #   amber  : error_rate 5-25%
    #   red    : error_rate >= 25%  OR last 3 runs all failed
    last3 = sorted(rows, key=lambda r: r.started_at, reverse=True)[:3]
    last3_all_failed = len(last3) >= 3 and all(r.status == "failed" for r in last3)
    if error_rate >= 0.25 or last3_all_failed:
        alert = "red"
    elif error_rate >= 0.05:
        alert = "amber"
    else:
        alert = "green"
    return {
        "lookback_hours": lookback_hours,
        "runs": total,
        "success": success,
        "failed": failed,
        "running": running,
        "error_rate": round(error_rate, 4),
        "avg_duration_seconds": round(avg_duration, 2),
        "last_failure_at": last_failure.isoformat() if last_failure else None,
        "last_success_at": last_success.isoformat() if last_success else None,
        "alert": alert,
    }
