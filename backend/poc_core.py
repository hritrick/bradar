"""
POC: Business Radar AI - Core Workflow Validation
Tests in isolation:
1. PostgreSQL connection (async SQLAlchemy + asyncpg)
2. Schema creation
3. CRUD on businesses
4. AI enrichment (structured JSON)
5. AI prediction of service needs (structured JSON)
6. AI lead scoring (structured JSON)
7. PDF report generation (ReportLab)
8. Excel + CSV export
"""
import asyncio
import json
import os
import sys
import traceback
import uuid
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

DB_URL = os.environ["DATABASE_URL"]
LLM_KEY = os.environ["EMERGENT_LLM_KEY"]

# ---------- 1. DB layer ----------
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Float,
    Integer,
    ForeignKey,
    Text,
    Date,
    JSON,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Business(Base):
    __tablename__ = "poc_businesses"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_name = Column(String(255), nullable=False)
    registration_date = Column(Date, nullable=True)
    company_type = Column(String(80))
    category = Column(String(120))
    sub_category = Column(String(120))
    website = Column(String(255))
    phone = Column(String(40))
    email = Column(String(120))
    address = Column(Text)
    city = Column(String(80))
    state = Column(String(80))
    pincode = Column(String(15))
    source = Column(String(80))
    confidence_score = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.utcnow)


class Prediction(Base):
    __tablename__ = "poc_predictions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, ForeignKey("poc_businesses.id"))
    predicted_need = Column(String(120))
    probability = Column(Float)
    reasoning = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class LeadScore(Base):
    __tablename__ = "poc_lead_scores"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = Column(String, ForeignKey("poc_businesses.id"))
    score = Column(Integer)
    lead_category = Column(String(20))
    scoring_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------- 2. AI Service via emergentintegrations ----------
from emergentintegrations.llm.chat import LlmChat, UserMessage


async def llm_json(system_prompt: str, user_prompt: str, model_provider="openai", model_name="gpt-4o-mini") -> dict:
    """Call LLM and force JSON response."""
    session_id = f"poc-{uuid.uuid4()}"
    chat = (
        LlmChat(api_key=LLM_KEY, session_id=session_id, system_message=system_prompt)
        .with_model(model_provider, model_name)
    )
    msg = UserMessage(text=user_prompt + "\n\nRespond with ONLY a valid JSON object. No prose, no markdown fences.")
    raw = await chat.send_message(msg)
    text = raw.strip()
    if text.startswith("```"):
        # strip markdown fences
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    # try to locate first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object in LLM output: {raw}")
    return json.loads(text[start : end + 1])


async def enrich_business(b: dict) -> dict:
    system = (
        "You are a business data enrichment expert for the Indian market. "
        "Given partial business data, infer/fill missing fields realistically. "
        "Output strict JSON."
    )
    user = (
        "Enrich this business and output JSON with EXACT keys: "
        "category (string), sub_category (string), company_type (string, e.g., Private Limited, LLP, Sole Proprietorship), "
        "employee_estimate (integer), confidence_score (float between 0 and 1). "
        f"\nBusiness data: {json.dumps(b, default=str)}"
    )
    return await llm_json(system, user)


async def predict_needs(b: dict) -> dict:
    system = (
        "You are a B2B service-need prediction expert. "
        "Given a business profile, identify the MOST LIKELY service need they will require in the next 6 months. "
        "Output strict JSON."
    )
    user = (
        "Output JSON with EXACT keys: "
        "predicted_need (string, e.g., 'Accounting & Compliance', 'Digital Marketing', 'GST Registration'), "
        "probability (float 0-1), "
        "reasoning (string, 1-2 sentences). "
        f"\nBusiness: {json.dumps(b, default=str)}"
    )
    return await llm_json(system, user)


async def score_lead(b: dict) -> dict:
    system = (
        "You are a lead-quality scoring expert for Indian B2B service providers. "
        "Score the lead 0-100 based on business size signals, completeness, recency, and category attractiveness."
    )
    user = (
        "Output JSON with EXACT keys: "
        "score (integer 0-100), "
        "lead_category (string: HOT if score>=75, WARM if 50-74, COLD if <50), "
        "scoring_reason (string, 1-2 sentences). "
        f"\nBusiness: {json.dumps(b, default=str)}"
    )
    return await llm_json(system, user)


# ---------- 3. PDF + Excel + CSV ----------
def generate_pdf_report(filepath: Path, businesses: list):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )

    doc = SimpleDocTemplate(str(filepath), pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph("Business Radar AI - Daily Report (POC)", styles["Title"]))
    elements.append(Paragraph(f"Generated: {datetime.utcnow().isoformat()}", styles["Normal"]))
    elements.append(Spacer(1, 12))
    data = [["Business", "City", "Category", "Score", "Lead"]]
    for b in businesses:
        data.append([b.get("name"), b.get("city"), b.get("category"), b.get("score"), b.get("lead_category")])
    table = Table(data, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)


def generate_excel_export(filepath: Path, businesses: list):
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Businesses"
    ws.append(["Business", "City", "Category", "Score", "Lead"])
    for b in businesses:
        ws.append([b.get("name"), b.get("city"), b.get("category"), b.get("score"), b.get("lead_category")])
    wb.save(str(filepath))


def generate_csv_export(filepath: Path, businesses: list):
    import csv

    with open(filepath, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Business", "City", "Category", "Score", "Lead"])
        for b in businesses:
            w.writerow([b.get("name"), b.get("city"), b.get("category"), b.get("score"), b.get("lead_category")])


# ---------- 4. Main POC flow ----------
async def main():
    results = {}

    # --- DB connectivity + schema ---
    print("\n[1/5] Testing PostgreSQL connection and schema...")
    engine = create_async_engine(DB_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("  ✓ Schema created")
    results["db"] = "OK"

    # --- Insert seed business ---
    seed = Business(
        business_name="Innov8 Logistics Pvt Ltd",
        registration_date=date(2025, 10, 15),
        company_type="Private Limited",
        website="https://innov8logistics.in",
        phone="+91-9876543210",
        email="hello@innov8logistics.in",
        address="A-101, Thane West",
        city="Thane",
        state="Maharashtra",
        pincode="400601",
        source="manual",
        confidence_score=0.6,
    )
    async with SessionLocal() as s:
        s.add(seed)
        await s.commit()
        await s.refresh(seed)
        print(f"  ✓ Inserted business id={seed.id}")
        b_dict = {
            "business_name": seed.business_name,
            "city": seed.city,
            "state": seed.state,
            "pincode": seed.pincode,
            "company_type": seed.company_type,
            "website": seed.website,
            "registration_date": str(seed.registration_date),
        }

    # --- AI Enrichment ---
    print("\n[2/5] Testing AI enrichment...")
    try:
        enriched = await enrich_business(b_dict)
        print(f"  ✓ Enrich: {enriched}")
        assert "category" in enriched
        results["enrich"] = "OK"
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        traceback.print_exc()
        results["enrich"] = f"FAIL: {e}"
        return results

    # --- AI Prediction ---
    print("\n[3/5] Testing AI prediction of service needs...")
    try:
        b_dict.update(enriched)
        pred = await predict_needs(b_dict)
        print(f"  ✓ Predict: {pred}")
        assert "predicted_need" in pred and "probability" in pred
        results["predict"] = "OK"
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        traceback.print_exc()
        results["predict"] = f"FAIL: {e}"
        return results

    # --- AI Lead Score ---
    print("\n[4/5] Testing AI lead scoring...")
    try:
        score = await score_lead(b_dict)
        print(f"  ✓ Score: {score}")
        assert "score" in score and "lead_category" in score
        results["score"] = "OK"
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        traceback.print_exc()
        results["score"] = f"FAIL: {e}"
        return results

    # Persist predictions + scores
    async with SessionLocal() as s:
        p = Prediction(
            business_id=seed.id,
            predicted_need=pred["predicted_need"],
            probability=float(pred["probability"]),
            reasoning=pred.get("reasoning", ""),
        )
        ls = LeadScore(
            business_id=seed.id,
            score=int(score["score"]),
            lead_category=score["lead_category"],
            scoring_reason=score.get("scoring_reason", ""),
        )
        s.add_all([p, ls])
        await s.commit()
        print("  ✓ Persisted prediction + lead score rows")

    # --- Generate PDF + Excel + CSV ---
    print("\n[5/5] Testing report generation (PDF/Excel/CSV)...")
    out_dir = ROOT / "poc_out"
    out_dir.mkdir(exist_ok=True)
    businesses_for_report = [
        {
            "name": seed.business_name,
            "city": seed.city,
            "category": enriched.get("category"),
            "score": score["score"],
            "lead_category": score["lead_category"],
        }
    ]
    try:
        pdf_path = out_dir / "daily_report.pdf"
        generate_pdf_report(pdf_path, businesses_for_report)
        assert pdf_path.stat().st_size > 0
        print(f"  ✓ PDF: {pdf_path} ({pdf_path.stat().st_size} bytes)")

        xlsx_path = out_dir / "export.xlsx"
        generate_excel_export(xlsx_path, businesses_for_report)
        assert xlsx_path.stat().st_size > 0
        print(f"  ✓ Excel: {xlsx_path} ({xlsx_path.stat().st_size} bytes)")

        csv_path = out_dir / "export.csv"
        generate_csv_export(csv_path, businesses_for_report)
        assert csv_path.stat().st_size > 0
        print(f"  ✓ CSV: {csv_path} ({csv_path.stat().st_size} bytes)")
        results["reports"] = "OK"
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        traceback.print_exc()
        results["reports"] = f"FAIL: {e}"
        return results

    print("\n========== POC SUMMARY ==========")
    for k, v in results.items():
        print(f"  {k:10s}: {v}")
    print("=================================")
    return results


if __name__ == "__main__":
    res = asyncio.run(main())
    failures = [k for k, v in res.items() if not v.startswith("OK")]
    if failures:
        print(f"\n!!! FAILED: {failures}")
        sys.exit(1)
    print("\n*** ALL CORE CHECKS PASSED ***")
    sys.exit(0)
