"""APScheduler-based daily report job + dynamic per-source discovery jobs."""
import logging
import os
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from database import SessionLocal
from models import DailyReport, SchedulerJobRun, DiscoverySource
from reports_service import build_report_data, generate_pdf
from storage_service import get_storage
from settings_service import get_setting

log = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


async def generate_today_report_job():
    run = SchedulerJobRun(job_name="daily_report", status="running")
    async with SessionLocal() as db:
        db.add(run)
        await db.commit()
        await db.refresh(run)
    try:
        async with SessionLocal() as db:
            data = await build_report_data(db, report_date=date.today())
            res = await db.execute(select(DailyReport).where(DailyReport.report_date == date.today()))
            existing = res.scalar_one_or_none()
            pdf_bytes = generate_pdf(data)
            uri = get_storage().put(
                key=f"daily-reports/daily_{date.today().isoformat()}.pdf",
                data=pdf_bytes,
                content_type="application/pdf",
            )
            if existing:
                existing.report_json = data
                existing.report_pdf = uri
            else:
                db.add(DailyReport(report_date=date.today(), report_json=data, report_pdf=uri, generated_by="scheduler"))
            await db.commit()
        async with SessionLocal() as db2:
            rr = await db2.execute(select(SchedulerJobRun).where(SchedulerJobRun.id == run.id))
            row = rr.scalar_one()
            row.status = "success"
            row.finished_at = datetime.utcnow()
            row.message = f"Report for {date.today()} generated and stored at {uri}."
            await db2.commit()
        log.info(f"Daily report generated for {date.today()} at {uri}")
    except Exception as e:
        log.exception("Scheduler job failed")
        async with SessionLocal() as db2:
            rr = await db2.execute(select(SchedulerJobRun).where(SchedulerJobRun.id == run.id))
            row = rr.scalar_one()
            row.status = "failed"
            row.finished_at = datetime.utcnow()
            row.message = str(e)
            await db2.commit()


async def _discovery_source_job(source_name: str):
    """Wrapper that calls the discovery router execute helper."""
    try:
        # Import here to avoid circular import at module load.
        from routers.discovery_router import _execute_run
        res = await _execute_run(source_name, limit=20, query=None, triggered_by="scheduler")
        log.info("scheduled discovery: %s -> %s", source_name, res)
    except Exception as e:
        log.exception("scheduled discovery %s failed: %s", source_name, e)


async def register_source_schedules():
    """Read enabled DiscoverySource rows with a schedule_cron and register/refresh APScheduler jobs.

    Safe to call repeatedly: existing jobs are replaced.
    """
    async with SessionLocal() as db:
        srcs = (await db.execute(
            select(DiscoverySource).where(DiscoverySource.enabled.is_(True))
        )).scalars().all()
    # First, remove any previously-registered discovery jobs whose source no longer has a schedule
    existing_ids = {j.id for j in scheduler.get_jobs() if j.id and j.id.startswith("discovery:")}
    desired_ids = set()
    for s in srcs:
        if not s.schedule_cron:
            continue
        cron = s.schedule_cron.strip()
        try:
            trig = CronTrigger.from_crontab(cron, timezone="Asia/Kolkata")
        except Exception as e:
            log.warning("bad cron for %s: %r (%s) — skipping", s.name, cron, e)
            continue
        job_id = f"discovery:{s.name}"
        desired_ids.add(job_id)
        scheduler.add_job(_discovery_source_job, trig, args=[s.name], id=job_id, replace_existing=True)
        log.info("registered discovery schedule: %s @ %s IST", s.name, cron)
    # Remove orphan jobs (source disabled or cron cleared)
    for jid in existing_ids - desired_ids:
        try:
            scheduler.remove_job(jid)
            log.info("removed orphan schedule: %s", jid)
        except Exception:
            pass


async def start_scheduler():
    cron_time = (await get_setting("daily_report_time")) or "08:00"
    try:
        hh, mm = cron_time.split(":")
        scheduler.add_job(
            generate_today_report_job,
            CronTrigger(hour=int(hh), minute=int(mm), timezone="Asia/Kolkata"),
            id="daily_report",
            replace_existing=True,
        )
        # Register dynamic discovery cron jobs from DB
        await register_source_schedules()
        scheduler.start()
        log.info(f"Scheduler started; daily report at {cron_time} IST; discovery schedules registered.")
    except Exception as e:
        log.warning(f"Could not start scheduler: {e}")


async def stop_scheduler():
    try:
        scheduler.shutdown(wait=False)
    except Exception:
        pass
