"""Settings + audit logs + scheduler routes."""
from fastapi import APIRouter, Depends, Request, Query
from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User, AuditLog, SchedulerJobRun
from schemas import SettingsUpdate, AuditLogOut
from deps import require_roles, get_current_user
from settings_service import get_all_settings_masked, update_settings
from audit import write_audit
import scheduler as scheduler_mod

router = APIRouter(tags=["admin"])
ADMIN = require_roles(["Admin"])


@router.get("/settings")
async def get_settings(_: User = Depends(ADMIN)):
    return await get_all_settings_masked()


@router.patch("/settings")
async def patch_settings(body: SettingsUpdate, request: Request, db: AsyncSession = Depends(get_db), me: User = Depends(ADMIN)):
    await update_settings(body.settings)
    await write_audit(db, user_id=me.id, user_email=me.email, action="update_settings", entity_type="settings",
                      after_value={k: ("••••••••" if k.endswith("secret") or "password" in k or "token" in k or "api_key" in k else v) for k, v in body.settings.items()},
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
    return await get_all_settings_masked()


@router.get("/audit-logs", response_model=List[AuditLogOut])
async def list_audit(
    db: AsyncSession = Depends(get_db), _: User = Depends(ADMIN),
    action: Optional[str] = None, entity_type: Optional[str] = None, user_email: Optional[str] = None,
    limit: int = 200,
):
    stmt = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(min(1000, max(1, limit)))
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if user_email:
        stmt = stmt.where(AuditLog.user_email == user_email)
    res = await db.execute(stmt)
    return [AuditLogOut.model_validate(r) for r in res.scalars()]


@router.get("/scheduler/status")
async def scheduler_status(db: AsyncSession = Depends(get_db), _: User = Depends(ADMIN)):
    res = await db.execute(select(SchedulerJobRun).order_by(desc(SchedulerJobRun.started_at)).limit(20))
    runs = [
        {
            "id": r.id, "job_name": r.job_name, "status": r.status,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "message": r.message,
        }
        for r in res.scalars()
    ]
    next_run = None
    try:
        for job in scheduler_mod.scheduler.get_jobs():
            if job.id == "daily_report" and job.next_run_time:
                next_run = job.next_run_time.isoformat()
    except Exception:
        pass
    return {"running": scheduler_mod.scheduler.running, "next_run": next_run, "recent_runs": runs}


@router.post("/scheduler/run-now")
async def run_now(request: Request, db: AsyncSession = Depends(get_db), me: User = Depends(ADMIN)):
    await scheduler_mod.generate_today_report_job()
    await write_audit(db, user_id=me.id, user_email=me.email, action="scheduler_run_now", entity_type="scheduler",
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
    return {"ok": True}
