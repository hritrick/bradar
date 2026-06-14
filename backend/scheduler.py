"""APScheduler-based daily report job."""
import logging
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from database import SessionLocal
from models import DailyReport, SchedulerJobRun
from reports_service import build_report_data, generate_pdf, REPORTS_DIR
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
            pdf_path = REPORTS_DIR / f"daily_{date.today().isoformat()}.pdf"
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
            if existing:
                existing.report_json = data
                existing.report_pdf = str(pdf_path)
            else:
                db.add(DailyReport(report_date=date.today(), report_json=data, report_pdf=str(pdf_path), generated_by="scheduler"))
            await db.commit()
            async with SessionLocal() as db2:
                rr = await db2.execute(select(SchedulerJobRun).where(SchedulerJobRun.id == run.id))
                row = rr.scalar_one()
                row.status = "success"
                row.finished_at = datetime.utcnow()
                row.message = f"Report for {date.today()} generated."
                await db2.commit()
            log.info(f"Daily report generated for {date.today()}")
    except Exception as e:
        log.exception("Scheduler job failed")
        async with SessionLocal() as db2:
            rr = await db2.execute(select(SchedulerJobRun).where(SchedulerJobRun.id == run.id))
            row = rr.scalar_one()
            row.status = "failed"
            row.finished_at = datetime.utcnow()
            row.message = str(e)
            await db2.commit()


async def start_scheduler():
    cron_time = (await get_setting("daily_report_time")) or "08:00"
    try:
        hh, mm = cron_time.split(":")
        scheduler.add_job(
            generate_today_report_job,
            CronTrigger(hour=int(hh), minute=int(mm)),
            id="daily_report",
            replace_existing=True,
        )
        scheduler.start()
        log.info(f"Scheduler started; daily report at {cron_time} IST")
    except Exception as e:
        log.warning(f"Could not start scheduler: {e}")


async def stop_scheduler():
    try:
        scheduler.shutdown(wait=False)
    except Exception:
        pass
