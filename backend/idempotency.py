"""Idempotency support for write endpoints.

Usage:
    from idempotency import check_or_record
    cached = await check_or_record(key, scope="discovery_run", payload=body)
    if cached: return cached
    ... do work ...
    await idempotency_store_result(key, scope, response_dict)

Keys are scoped (so the same Idempotency-Key can be reused across different endpoints).
Expiry default 24h.
"""
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from sqlalchemy import select
from database import SessionLocal
from models import IdempotencyKey

log = logging.getLogger(__name__)
DEFAULT_TTL_HOURS = 24


def _hash_payload(payload: Any) -> str:
    try:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    except Exception:
        return hashlib.sha256(str(payload).encode()).hexdigest()


async def check_or_record(key: str, scope: str, payload: Any, ttl_hours: int = DEFAULT_TTL_HOURS) -> Optional[dict]:
    """If key+scope already used, return cached response (when same payload); else record pending and return None.

    If a different payload is replayed under the same key, raise to prevent silent overwrites.
    """
    payload_hash = _hash_payload(payload)
    async with SessionLocal() as db:
        existing = (await db.execute(
            select(IdempotencyKey).where(
                IdempotencyKey.key == key, IdempotencyKey.scope == scope
            )
        )).scalar_one_or_none()
        now = datetime.utcnow()
        if existing:
            if existing.expires_at and existing.expires_at < now:
                await db.delete(existing); await db.commit()
            else:
                if existing.payload_hash != payload_hash:
                    from fastapi import HTTPException, status
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Idempotency-Key reused with a different payload",
                    )
                # Same payload — return cached result (or empty dict if still pending)
                return existing.response or {"pending": True}
        # No prior key — record pending
        row = IdempotencyKey(
            key=key, scope=scope, payload_hash=payload_hash,
            response=None, created_at=now,
            expires_at=now + timedelta(hours=ttl_hours),
        )
        db.add(row)
        try:
            await db.commit()
        except Exception as e:
            log.warning("idempotency record failed: %s", e)
        return None


async def store_result(key: str, scope: str, response: dict) -> None:
    async with SessionLocal() as db:
        row = (await db.execute(
            select(IdempotencyKey).where(
                IdempotencyKey.key == key, IdempotencyKey.scope == scope
            )
        )).scalar_one_or_none()
        if row:
            row.response = response
            await db.commit()
