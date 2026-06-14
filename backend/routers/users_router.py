"""Users CRUD (Admin)."""
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User, UserPreference
from schemas import UserOut, UserCreateRequest, UserUpdateRequest
from security import hash_password
from deps import require_roles
from audit import write_audit

router = APIRouter(prefix="/users", tags=["users"])

ADMIN = require_roles(["Admin"])


@router.get("", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db), _: User = Depends(ADMIN)):
    res = await db.execute(select(User).order_by(User.created_at.desc()))
    return [UserOut.model_validate(u) for u in res.scalars()]


@router.post("", response_model=dict, status_code=201)
async def create_user(body: UserCreateRequest, request: Request, db: AsyncSession = Depends(get_db), me: User = Depends(ADMIN)):
    if body.role not in ("Admin", "Analyst", "Subscriber"):
        raise HTTPException(400, "Invalid role")
    existing = await db.execute(select(User).where(User.email == body.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Email already exists")
    temp_pwd = body.password or secrets.token_urlsafe(8)
    user = User(
        name=body.name,
        email=body.email.lower(),
        role=body.role,
        status="Active",
        password_hash=hash_password(temp_pwd),
        force_password_reset=True,
    )
    db.add(user)
    await db.flush()
    db.add(UserPreference(user_id=user.id, delivery_email=user.email))
    await db.commit()
    await db.refresh(user)
    await write_audit(db, user_id=me.id, user_email=me.email, action="create_user", entity_type="user", entity_id=user.id,
                      after_value={"name": user.name, "email": user.email, "role": user.role},
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
    return {"user": UserOut.model_validate(user).model_dump(), "temporary_password": temp_pwd}


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: str, body: UserUpdateRequest, request: Request, db: AsyncSession = Depends(get_db), me: User = Depends(ADMIN)):
    res = await db.execute(select(User).where(User.id == user_id))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    before = {"name": u.name, "role": u.role, "status": u.status}
    if body.name is not None:
        u.name = body.name
    if body.role is not None:
        if body.role not in ("Admin", "Analyst", "Subscriber"):
            raise HTTPException(400, "Invalid role")
        u.role = body.role
    if body.status is not None:
        u.status = body.status
    await db.commit()
    await db.refresh(u)
    await write_audit(db, user_id=me.id, user_email=me.email, action="update_user", entity_type="user", entity_id=u.id,
                      before_value=before, after_value={"name": u.name, "role": u.role, "status": u.status},
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
    return UserOut.model_validate(u)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: str, request: Request, db: AsyncSession = Depends(get_db), me: User = Depends(ADMIN)):
    if user_id == me.id:
        raise HTTPException(400, "Cannot delete yourself")
    res = await db.execute(select(User).where(User.id == user_id))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    email = u.email
    await db.delete(u)
    await db.commit()
    await write_audit(db, user_id=me.id, user_email=me.email, action="delete_user", entity_type="user", entity_id=user_id,
                      before_value={"email": email},
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
