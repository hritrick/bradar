"""Singleton-style settings via key/value rows."""
from typing import Optional, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal
from models import Settings

SECRET_KEYS = {
    "google_oauth_client_secret",
    "sendgrid_api_key",
    "smtp_password",
    "opencorporates_api_token",
}

SETTING_KEYS = [
    "google_oauth_client_id",
    "google_oauth_client_secret",
    "google_oauth_redirect_uri",
    "sendgrid_api_key",
    "sender_email",
    "sender_name",
    "smtp_host",
    "smtp_port",
    "smtp_user",
    "smtp_password",
    "email_provider",
    "opencorporates_api_token",
    "daily_report_time",  # HH:MM 24h
]


async def get_setting(key: str) -> Optional[str]:
    async with SessionLocal() as db:
        res = await db.execute(select(Settings).where(Settings.key == key))
        row = res.scalar_one_or_none()
        return row.value if row else None


async def get_all_settings_masked() -> Dict[str, dict]:
    out = {}
    async with SessionLocal() as db:
        res = await db.execute(select(Settings))
        rows = {r.key: r for r in res.scalars().all()}
    for k in SETTING_KEYS:
        row = rows.get(k)
        value = row.value if row else None
        is_secret = k in SECRET_KEYS
        displayed = None
        configured = bool(value)
        if value and is_secret:
            displayed = "•••••••• " + (value[-4:] if len(value) > 4 else "")
        elif value:
            displayed = value
        out[k] = {"value": displayed, "is_secret": is_secret, "configured": configured}
    return out


async def update_settings(items: Dict[str, Optional[str]]) -> None:
    async with SessionLocal() as db:
        res = await db.execute(select(Settings))
        existing = {r.key: r for r in res.scalars().all()}
        for k, v in items.items():
            if k not in SETTING_KEYS:
                continue
            # Ignore unchanged masked values
            if v is None or v == "":
                # treat empty string as 'clear'
                if v == "":
                    if k in existing:
                        existing[k].value = None
                continue
            if v.startswith("•"):
                # masked placeholder, skip
                continue
            is_secret = k in SECRET_KEYS
            if k in existing:
                existing[k].value = v
                existing[k].is_secret = is_secret
            else:
                db.add(Settings(key=k, value=v, is_secret=is_secret))
        await db.commit()
