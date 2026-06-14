"""Seed: admin users, QA users, and ~10,000 synthetic Mumbai/Thane/Navi Mumbai businesses."""
import asyncio
import logging
import os
import random
import secrets
from datetime import datetime, date
from typing import List, Dict, Any
from sqlalchemy import select, func, insert
from database import SessionLocal, engine
from models import (
    User, Business, UserPreference, Prediction, LeadScore,
    Settings, DiscoverySource, EnrichmentQueueItem,
)
from security import hash_password
from providers.synthetic import generate_synthetic_batch, INDUSTRIES

log = logging.getLogger(__name__)

ADMIN_EMAIL = os.environ.get("SEED_ADMIN_EMAIL", "dhananjay@businessradar.ai")
ADMIN_NAME = os.environ.get("SEED_ADMIN_NAME", "Dhananjay")
ADMIN_TEST_EMAIL = os.environ.get("TEST_LOGIN_EMAIL", "test.admin@businessradar.ai")
ADMIN_TEST_PASSWORD = os.environ.get("TEST_LOGIN_PASSWORD", "RadarTest@2025")
TARGET_BUSINESS_COUNT = int(os.environ.get("SEED_TARGET_COUNT", "10000"))

PRED_BY_INDUSTRY = {
    "Real Estate": ["Legal & Compliance", "Digital Marketing", "Office Lease", "Branding & Web"],
    "Manufacturing": ["GST Registration", "Logistics Tech", "ERP Software", "HR & Payroll"],
    "Logistics": ["Cloud Hosting", "Insurance", "GST Registration", "IT Infrastructure"],
    "Retail": ["Digital Marketing", "Payment Gateway", "POS Systems", "Branding & Web"],
    "IT Services": ["Cloud Hosting", "HR & Payroll", "Branding & Web", "Legal & Trademark"],
    "Healthcare": ["Compliance", "EHR Software", "Digital Marketing", "IT Infrastructure"],
}


def _synth_score_and_pred(industry: str, employee_estimate: int, days_since_reg: int):
    # Bias scores by industry attractiveness and recency
    base = {
        "IT Services": 70, "Healthcare": 64, "Logistics": 60, "Real Estate": 58, "Retail": 56, "Manufacturing": 62
    }.get(industry, 55)
    employee_boost = min(20, int((employee_estimate or 0) / 25))
    recency_boost = max(0, 12 - int(days_since_reg / 8))
    score = base + employee_boost + recency_boost + random.randint(-12, 12)
    score = max(5, min(99, score))
    cat = "HOT" if score >= 75 else "WARM" if score >= 50 else "COLD"
    pred = random.choice(PRED_BY_INDUSTRY.get(industry, ["Digital Marketing"]))
    prob = round(random.uniform(0.55, 0.92), 2)
    reason_score = f"{industry} business with ~{employee_estimate} employees, registered {days_since_reg}d ago."
    reason_pred = f"Recently registered {industry.lower()} firm likely to need {pred.lower()} based on size and category."
    return score, cat, pred, prob, reason_score, reason_pred


async def _ensure_users():
    async with SessionLocal() as db:
        # primary admin Dhananjay
        res = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        if not res.scalar_one_or_none():
            temp_pwd = secrets.token_urlsafe(10)
            admin = User(
                name=ADMIN_NAME, email=ADMIN_EMAIL, password_hash=hash_password(temp_pwd),
                role="Admin", status="Active", force_password_reset=True,
            )
            db.add(admin)
            await db.flush()
            db.add(UserPreference(user_id=admin.id, delivery_email=admin.email))
            await db.commit()
            print("=" * 64)
            print(f" SEED ADMIN CREATED\n   Email: {ADMIN_EMAIL}\n   Temp pwd: {temp_pwd}\n   force_password_reset=True")
            print("=" * 64, flush=True)
        # Test admin
        res = await db.execute(select(User).where(User.email == ADMIN_TEST_EMAIL))
        if not res.scalar_one_or_none():
            a = User(name="Test Admin", email=ADMIN_TEST_EMAIL, password_hash=hash_password(ADMIN_TEST_PASSWORD), role="Admin", status="Active")
            db.add(a); await db.flush()
            db.add(UserPreference(user_id=a.id, delivery_email=a.email))
            await db.commit()
            print("=" * 64)
            print(f" TEST ADMIN: {ADMIN_TEST_EMAIL} / {ADMIN_TEST_PASSWORD}")
            print("=" * 64, flush=True)
        for em, pwd, role, nm in [
            ("test.analyst@businessradar.ai", "AnalystTest@2025", "Analyst", "Test Analyst"),
            ("test.subscriber@businessradar.ai", "SubTest@2025", "Subscriber", "Test Subscriber"),
        ]:
            res = await db.execute(select(User).where(User.email == em))
            if not res.scalar_one_or_none():
                u = User(name=nm, email=em, password_hash=hash_password(pwd), role=role, status="Active")
                db.add(u); await db.flush()
                db.add(UserPreference(user_id=u.id, delivery_email=u.email))
                await db.commit()


async def _bulk_seed_businesses():
    async with SessionLocal() as db:
        existing = (await db.execute(select(func.count(Business.id)))).scalar() or 0
    if existing >= TARGET_BUSINESS_COUNT:
        log.info(f"Skip seed: {existing} businesses already present (target {TARGET_BUSINESS_COUNT}).")
        return
    needed = TARGET_BUSINESS_COUNT - existing
    log.info(f"Seeding {needed} synthetic businesses (existing={existing}).")

    # generate all rows then insert in chunks
    BATCH = 500
    total_inserted = 0
    for batch_start in range(0, needed, BATCH):
        rows = generate_synthetic_batch(min(BATCH, needed - batch_start))
        biz_dicts = []
        scoring = []
        from uuid import uuid4
        for r in rows:
            r["id"] = str(uuid4())
            r["enrichment_status"] = "enriched"  # synthetic enrichment baked-in
            r["created_at"] = datetime.utcnow()
            r["updated_at"] = datetime.utcnow()
            # truncate fields to model bounds
            for k in ("business_name",):
                if r.get(k) and len(r[k]) > 250:
                    r[k] = r[k][:250]
            # synth scoring + prediction
            days_since = (date.today() - r["registration_date"]).days
            score, cat, pred, prob, sr, pr = _synth_score_and_pred(r["industry"], r["employee_estimate"], days_since)
            scoring.append((r["id"], score, cat, pred, prob, sr, pr))
            biz_dicts.append({k: v for k, v in r.items() if k in {
                "id", "business_name", "gst_number", "registration_date", "company_type", "industry",
                "category", "sub_category", "website", "phone", "email", "linkedin_url", "director_name",
                "employee_estimate", "address", "locality", "city", "district", "state", "country",
                "pincode", "latitude", "longitude", "source", "source_url", "confidence_score",
                "enrichment_status", "created_at", "updated_at",
            }})
        pred_rows = []
        ls_rows = []
        from uuid import uuid4
        for (biz_id, score, cat, pred, prob, sr, pr) in scoring:
            pred_rows.append({
                "id": str(uuid4()), "business_id": biz_id, "predicted_need": pred,
                "probability": prob, "reasoning": pr, "model_used": "synthetic",
                "created_at": datetime.utcnow(),
            })
            ls_rows.append({
                "id": str(uuid4()), "business_id": biz_id, "score": score, "lead_category": cat,
                "scoring_reason": sr, "created_at": datetime.utcnow(),
            })
        async with engine.begin() as conn:
            await conn.execute(insert(Business.__table__), biz_dicts)
            await conn.execute(insert(Prediction.__table__), pred_rows)
            await conn.execute(insert(LeadScore.__table__), ls_rows)
        total_inserted += len(biz_dicts)
        log.info(f"Seeded {total_inserted}/{needed}…")
    log.info(f"Done seeding {total_inserted} synthetic businesses.")


async def _ensure_discovery_sources():
    from providers import provider_metadata
    metas = await provider_metadata()
    async with SessionLocal() as db:
        existing = {r.name: r for r in (await db.execute(select(DiscoverySource))).scalars().all()}
        for m in metas:
            if m["name"] in existing:
                continue
            db.add(DiscoverySource(
                name=m["name"], display_name=m["display_name"], description=m["description"],
                requires_config=m["requires_config"],
                enabled=(m["name"] in ("manual", "csv_import", "synthetic")),
            ))
        await db.commit()


async def run_seed():
    await _ensure_users()
    await _ensure_discovery_sources()
    await _bulk_seed_businesses()
