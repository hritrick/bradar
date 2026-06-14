"""Audit log helper."""
import logging
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from models import AuditLog

log = logging.getLogger(__name__)


async def write_audit(
    db: AsyncSession,
    *,
    user_id: Optional[str],
    user_email: Optional[str],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    before_value: Optional[Any] = None,
    after_value: Optional[Any] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    try:
        entry = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_value=before_value,
            after_value=after_value,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(entry)
        await db.commit()
    except Exception as e:
        log.warning(f"Failed to write audit log: {e}")
