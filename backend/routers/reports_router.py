"""Daily Reports routes — backed by pluggable storage (local or S3-compatible)."""
import io
from datetime import date as DateT
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import DailyReport, User
from schemas import DailyReportOut, DailyReportListItem, GenerateReportRequest
from deps import get_current_user, require_roles
from reports_service import build_report_data, generate_pdf, fetch_businesses_for_export, businesses_to_csv, businesses_to_xlsx
from storage_service import get_storage
from audit import write_audit

router = APIRouter(prefix="/reports", tags=["reports"])


def _read_pdf(report: DailyReport) -> bytes:
    storage = get_storage()
    uri = report.report_pdf
    if uri and storage.exists(uri):
        return storage.get(uri)
    # Regenerate on miss (e.g. local file deleted, or migrating from disk to S3).
    return generate_pdf(report.report_json or {})


async def _persist_pdf(report: DailyReport, data: dict) -> str:
    pdf_bytes = generate_pdf(data)
    uri = get_storage().put(
        key=f"daily-reports/daily_{report.report_date.isoformat()}.pdf",
        data=pdf_bytes, content_type="application/pdf",
    )
    return uri


@router.get("", response_model=list[DailyReportListItem])
async def list_reports(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    res = await db.execute(select(DailyReport).order_by(desc(DailyReport.report_date)).limit(60))
    return [DailyReportListItem.model_validate(r) for r in res.scalars()]


@router.get("/today", response_model=DailyReportOut)
async def get_today(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    res = await db.execute(select(DailyReport).where(DailyReport.report_date == DateT.today()))
    rep = res.scalar_one_or_none()
    if not rep:
        data = await build_report_data(db, report_date=DateT.today())
        rep = DailyReport(report_date=DateT.today(), report_json=data, generated_by=user.email)
        rep.report_pdf = await _persist_pdf(rep, data)
        db.add(rep)
        await db.commit()
        await db.refresh(rep)
    return DailyReportOut.model_validate(rep)


@router.post("/generate", response_model=DailyReportOut)
async def generate(body: GenerateReportRequest, request: Request, db: AsyncSession = Depends(get_db), me: User = Depends(require_roles(["Admin", "Analyst"]))):
    target_date = body.report_date or DateT.today()
    data = await build_report_data(db, report_date=target_date, filters=body.filters)
    res = await db.execute(select(DailyReport).where(DailyReport.report_date == target_date))
    rep = res.scalar_one_or_none()
    if rep:
        rep.report_json = data
        rep.filters_applied = body.filters or {}
        rep.generated_by = me.email
    else:
        rep = DailyReport(report_date=target_date, report_json=data, filters_applied=body.filters or {}, generated_by=me.email)
        db.add(rep)
        await db.flush()
    rep.report_pdf = await _persist_pdf(rep, data)
    await db.commit()
    await db.refresh(rep)
    await write_audit(db, user_id=me.id, user_email=me.email, action="generate_report", entity_type="daily_report",
                      entity_id=rep.id, after_value={"report_date": str(target_date), "pdf_uri": rep.report_pdf},
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
    return DailyReportOut.model_validate(rep)


@router.get("/{report_id}", response_model=DailyReportOut)
async def get_report(report_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    res = await db.execute(select(DailyReport).where(DailyReport.id == report_id))
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Not found")
    return DailyReportOut.model_validate(r)


@router.get("/{report_id}/download/pdf")
async def download_pdf(report_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    res = await db.execute(select(DailyReport).where(DailyReport.id == report_id))
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Not found")
    data = _read_pdf(r)
    return StreamingResponse(io.BytesIO(data), media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename=report-{r.report_date}.pdf"})


@router.get("/{report_id}/download/csv")
async def download_csv(report_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    res = await db.execute(select(DailyReport).where(DailyReport.id == report_id))
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Not found")
    today_rows = (r.report_json or {}).get("today_list", [])
    return StreamingResponse(io.BytesIO(businesses_to_csv(today_rows)), media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename=report-{r.report_date}.csv"})


@router.get("/{report_id}/download/xlsx")
async def download_xlsx(report_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    res = await db.execute(select(DailyReport).where(DailyReport.id == report_id))
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Not found")
    today_rows = (r.report_json or {}).get("today_list", [])
    return StreamingResponse(io.BytesIO(businesses_to_xlsx(today_rows)),
                             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f"attachment; filename=report-{r.report_date}.xlsx"})


@router.get("/{report_id}/signed-url")
async def signed_url(report_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    """Returns a short-lived signed URL when the storage backend supports it (e.g. S3/R2).

    Falls back to {url:null} when storage is local-disk.
    """
    res = await db.execute(select(DailyReport).where(DailyReport.id == report_id))
    r = res.scalar_one_or_none()
    if not r or not r.report_pdf:
        raise HTTPException(404, "Not found")
    url = get_storage().signed_url(r.report_pdf, expires_seconds=600)
    return {"url": url, "expires_in": 600 if url else 0}
