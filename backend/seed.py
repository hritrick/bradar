"""Seed initial admin + a small set of demo businesses for Mumbai/Thane/Navi Mumbai."""
import asyncio
import logging
import os
import secrets
from datetime import date, timedelta
from sqlalchemy import select, func
from database import SessionLocal
from models import User, Business, UserPreference, Prediction, LeadScore, Settings
from security import hash_password
from discovery import SampleSeedConnector
from pipeline import ingest_business

log = logging.getLogger(__name__)

ADMIN_EMAIL = os.environ.get("SEED_ADMIN_EMAIL", "dhananjay@businessradar.ai")
ADMIN_NAME = os.environ.get("SEED_ADMIN_NAME", "Dhananjay")
ADMIN_TEST_EMAIL = os.environ.get("TEST_LOGIN_EMAIL", "test.admin@businessradar.ai")
ADMIN_TEST_PASSWORD = os.environ.get("TEST_LOGIN_PASSWORD", "RadarTest@2025")


async def run_seed():
    """Idempotent seeding. Generates temp passwords on first creation and prints them prominently in logs."""
    async with SessionLocal() as db:
        # 1) Default admin (Dhananjay)
        res = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
        admin = res.scalar_one_or_none()
        if not admin:
            temp_pwd = secrets.token_urlsafe(10)
            admin = User(
                name=ADMIN_NAME,
                email=ADMIN_EMAIL,
                password_hash=hash_password(temp_pwd),
                role="Admin",
                status="Active",
                force_password_reset=True,
            )
            db.add(admin)
            await db.flush()
            db.add(UserPreference(user_id=admin.id, delivery_email=admin.email))
            await db.commit()
            await db.refresh(admin)
            border = "=" * 64
            print(
                f"\n{border}\n"
                f" SEED ADMIN CREATED\n"
                f"   Email   : {ADMIN_EMAIL}\n"
                f"   TempPwd : {temp_pwd}\n"
                f"   NOTE    : force_password_reset=True (reset on first login)\n"
                f"{border}\n",
                flush=True,
            )
        # 2) Test admin (for backend/frontend testing agent + manual QA)
        res = await db.execute(select(User).where(User.email == ADMIN_TEST_EMAIL))
        test_admin = res.scalar_one_or_none()
        if not test_admin:
            test_admin = User(
                name="Test Admin",
                email=ADMIN_TEST_EMAIL,
                password_hash=hash_password(ADMIN_TEST_PASSWORD),
                role="Admin",
                status="Active",
                force_password_reset=False,
            )
            db.add(test_admin)
            await db.flush()
            db.add(UserPreference(user_id=test_admin.id, delivery_email=test_admin.email))
            await db.commit()
            border = "=" * 64
            print(
                f"\n{border}\n"
                f" TEST ADMIN (for QA / testing agent)\n"
                f"   Email    : {ADMIN_TEST_EMAIL}\n"
                f"   Password : {ADMIN_TEST_PASSWORD}\n"
                f"   Role     : Admin (no forced reset)\n"
                f"{border}\n",
                flush=True,
            )
        # 3) Test analyst
        res = await db.execute(select(User).where(User.email == "test.analyst@businessradar.ai"))
        if not res.scalar_one_or_none():
            ana = User(name="Test Analyst", email="test.analyst@businessradar.ai",
                       password_hash=hash_password("AnalystTest@2025"), role="Analyst", status="Active")
            db.add(ana)
            await db.flush()
            db.add(UserPreference(user_id=ana.id, delivery_email=ana.email))
            await db.commit()
        # 4) Test subscriber
        res = await db.execute(select(User).where(User.email == "test.subscriber@businessradar.ai"))
        if not res.scalar_one_or_none():
            sub = User(name="Test Subscriber", email="test.subscriber@businessradar.ai",
                       password_hash=hash_password("SubTest@2025"), role="Subscriber", status="Active")
            db.add(sub)
            await db.flush()
            db.add(UserPreference(user_id=sub.id, delivery_email=sub.email))
            await db.commit()
        # 5) Sample businesses (only if table effectively empty)
        count = (await db.execute(select(func.count(Business.id)))).scalar() or 0
        if count >= 5:
            return
    # Run sample seed connector to insert ~15 businesses with AI enrichment
    connector = SampleSeedConnector()
    rows = await connector.fetch_businesses(limit=15)
    inserted = 0
    async with SessionLocal() as db:
        for r in rows:
            try:
                _, created = await ingest_business(db, r, run_ai=True)
                if created:
                    inserted += 1
            except Exception as e:
                log.warning(f"Seed ingest failed: {e}")
    log.info(f"Seed: inserted {inserted} businesses")
