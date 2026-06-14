"""User preferences routes."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import UserPreference, User
from schemas import UserPreferenceOut, UserPreferenceUpdate
from deps import get_current_user
from audit import write_audit

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=UserPreferenceOut)
async def get_prefs(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    res = await db.execute(select(UserPreference).where(UserPreference.user_id == user.id))
    p = res.scalar_one_or_none()
    if not p:
        p = UserPreference(user_id=user.id, delivery_email=user.email)
        db.add(p)
        await db.commit()
        await db.refresh(p)
    return UserPreferenceOut.model_validate(p)


@router.patch("", response_model=UserPreferenceOut)
async def update_prefs(body: UserPreferenceUpdate, request: Request,
                       db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    res = await db.execute(select(UserPreference).where(UserPreference.user_id == user.id))
    p = res.scalar_one_or_none()
    if not p:
        p = UserPreference(user_id=user.id, delivery_email=user.email)
        db.add(p)
        await db.flush()
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    await write_audit(db, user_id=user.id, user_email=user.email, action="update_preferences", entity_type="preferences", entity_id=p.id,
                      after_value=body.model_dump(),
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
    return UserPreferenceOut.model_validate(p)
