"""Seed: admin users, QA users (only in non-prod), and ~10,000 synthetic businesses.

Production-safe rules:
  * The primary admin (Dhananjay) is always seeded with a *temporary* random password
    that is printed once to backend logs; `force_password_reset=True`.
  * QA users (test.admin / test.analyst / test.subscriber) are ONLY created when
    APP_ENV is one of {development, dev, local, test, staging}.
  * In production, no well-known credentials are ever created.
"""
import asyncio
import logging
import os
import random
import secrets
from datetime import datetime, date
from sqlalchemy import select, func, insert
from database import SessionLocal, engine
from models import (
    User, Business, UserPreference, Prediction, LeadScore,
    Settings, DiscoverySource, EnrichmentQueueItem,
)
from security import hash_password
from providers.synthetic import generate_synthetic_batch

log = logging.getLogger(__name__)

ADMIN_EMAIL = os.environ.get("SEED_ADMIN_EMAIL", "dhananjay@businessradar.ai")
ADMIN_NAME = os.environ.get("SEED_ADMIN_NAME", "Dhananjay")
TARGET_BUSINESS_COUNT = int(os.environ.get("SEED_TARGET_COUNT", "10000"))
APP_ENV = (os.environ.get("APP_ENV") or "development").lower()
NON_PROD = APP_ENV in {"development", "dev", "local", "test", "staging"}

QA_USERS = [
    ("test.admin@businessradar.ai", "RadarTest@2025", "Admin", "Test Admin"),
    ("test.analyst@businessradar.ai", "AnalystTest@2025", "Analyst", "Test Analyst"),
    ("test.subscriber@businessradar.ai", "SubTest@2025", "Subscriber", "Test Subscriber"),
]

PRED_BY_INDUSTRY = {
    "Real Estate": ["Legal & Compliance", "Digital Marketing", "Office Lease", "Branding & Web"],
    "Manufacturing": ["GST Registration", "Logistics Tech", "ERP Software", "HR & Payroll"],
    "Logistics": ["Cloud Hosting", "Insurance", "GST Registration", "IT Infrastructure"],
    "Retail": ["Digital Marketing", "Payment Gateway", "POS Systems", "Branding & Web"],
    "IT Services": ["Cloud Hosting", "HR & Payroll", "Branding & Web", "Legal & Trademark"],
    "Healthcare": ["Compliance", "EHR Software", "Digital Marketing", "IT Infrastructure"],
}


def _synth_score_and_pred(industry, employee_estimate, days_since_reg):
    base = {"IT Services": 70, "Healthcare": 64, "Logistics": 60, "Real Estate": 58, "Retail": 56, "Manufacturing": 62}.get(industry, 55)
    employee_boost = min(20, int((employee_estimate or 0) / 25))
    recency_boost = max(0, 12 - int(days_since_reg / 8))
    score = base + employee_boost + recency_boost + random.randint(-12, 12)
    score = max(5, min(99, score))
    cat = "HOT" if score >= 75 else "WARM" if score >= 50 else "COLD"
    pred = random.choice(PRED_BY_INDUSTRY.get(industry, ["Digital Marketing"]))
    prob = round(random.uniform(0.55, 0.92), 2)
    return score, cat, pred, prob, f"{industry} business with ~{employee_estimate} employees, registered {days_since_reg}d ago.", \
           f"Recently registered {industry.lower()} firm likely to need {pred.lower()} based on size and category."


async def _ensure_users():
    async with SessionLocal() as db:
        # Primary admin (always)
        res = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        if not res.scalar_one_or_none():
            temp_pwd = secrets.token_urlsafe(10)
            admin = User(name=ADMIN_NAME, email=ADMIN_EMAIL, password_hash=hash_password(temp_pwd),
                         role="Admin", status="Active", force_password_reset=True)
            db.add(admin)
            await db.flush()
            db.add(UserPreference(user_id=admin.id, delivery_email=admin.email))
            await db.commit()
            border = "=" * 64
            print(f"\n{border}\n SEED ADMIN CREATED\n   Email   : {ADMIN_EMAIL}\n   TempPwd : {temp_pwd}\n   NOTE    : force_password_reset=True (reset on first login)\n{border}\n", flush=True)

        # QA users only in non-prod
        if NON_PROD:
            for em, pwd, role, nm in QA_USERS:
                res = await db.execute(select(User).where(User.email == em))
                if not res.scalar_one_or_none():
                    u = User(name=nm, email=em, password_hash=hash_password(pwd), role=role, status="Active")
                    db.add(u); await db.flush()
                    db.add(UserPreference(user_id=u.id, delivery_email=u.email))
                    await db.commit()
            log.info("Seeded QA users (APP_ENV=%s).", APP_ENV)
        else:
            log.info("APP_ENV=%s — skipping QA user seed for production safety.", APP_ENV)


async def _ensure_discovery_sources():
    from providers import provider_metadata
    metas = await provider_metadata()
    async with SessionLocal() as db:
        existing = {r.name: r for r in (await db.execute(select(DiscoverySource))).scalars().all()}
        for m in metas:
            if m["name"] in existing:
                continue
            db.add(DiscoverySource(name=m["name"], display_name=m["display_name"], description=m["description"],
                                   requires_config=m["requires_config"],
                                   enabled=(m["name"] in ("manual", "csv_import", "synthetic"))))
        await db.commit()


async def _bulk_seed_businesses():
    if TARGET_BUSINESS_COUNT <= 0:
        return
    async with SessionLocal() as db:
        existing = (await db.execute(select(func.count(Business.id)))).scalar() or 0
    if existing >= TARGET_BUSINESS_COUNT:
        log.info(f"Skip seed: {existing} businesses already present (target {TARGET_BUSINESS_COUNT}).")
        return
    needed = TARGET_BUSINESS_COUNT - existing
    log.info(f"Seeding {needed} synthetic businesses.")
    BATCH = 500
    total_inserted = 0
    from uuid import uuid4
    for batch_start in range(0, needed, BATCH):
        rows = generate_synthetic_batch(min(BATCH, needed - batch_start))
        biz_dicts, pred_rows, ls_rows = [], [], []
        for r in rows:
            biz_id = str(uuid4())
            r["id"] = biz_id
            r["enrichment_status"] = "enriched"
            r["created_at"] = datetime.utcnow()
            r["updated_at"] = datetime.utcnow()
            if len(r.get("business_name", "")) > 250:
                r["business_name"] = r["business_name"][:250]
            days_since = (date.today() - r["registration_date"]).days
            score, cat, pred, prob, sr, pr = _synth_score_and_pred(r["industry"], r["employee_estimate"], days_since)
            biz_dicts.append({k: v for k, v in r.items() if k in {
                "id", "business_name", "gst_number", "registration_date", "company_type", "industry",
                "category", "sub_category", "website", "phone", "email", "linkedin_url", "director_name",
                "employee_estimate", "address", "locality", "city", "district", "state", "country",
                "pincode", "latitude", "longitude", "source", "source_url", "confidence_score",
                "enrichment_status", "created_at", "updated_at",
            }})
            pred_rows.append({"id": str(uuid4()), "business_id": biz_id, "predicted_need": pred,
                              "probability": prob, "reasoning": pr, "model_used": "synthetic",
                              "created_at": datetime.utcnow()})
            ls_rows.append({"id": str(uuid4()), "business_id": biz_id, "score": score, "lead_category": cat,
                            "scoring_reason": sr, "created_at": datetime.utcnow()})
        async with engine.begin() as conn:
            await conn.execute(insert(Business.__table__), biz_dicts)
            await conn.execute(insert(Prediction.__table__), pred_rows)
            await conn.execute(insert(LeadScore.__table__), ls_rows)
        total_inserted += len(biz_dicts)
        log.info(f"Seeded {total_inserted}/{needed}…")
    log.info(f"Done seeding {total_inserted} synthetic businesses.")


async def run_seed():
    await _ensure_users()
    await _ensure_discovery_sources()
    if NON_PROD:
        await _bulk_seed_businesses()
    else:
        log.info("APP_ENV=%s — skipping synthetic 10k seed for production safety.", APP_ENV)
