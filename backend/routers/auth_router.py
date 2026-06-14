"""Auth routes — with login rate limiting on /login."""
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User, UserPreference
from schemas import LoginRequest, Token, UserOut, PasswordResetRequest
from security import verify_password, hash_password, create_access_token
from deps import get_current_user
from audit import write_audit
from settings_service import get_setting
from rate_limit import rate_limit_login, rate_limit_clear_login

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Rate-limit by client IP (burst + per-minute). Raises HTTP 429 if exceeded.
    rate_limit_login(request)
    res = await db.execute(select(User).where(User.email == body.email.lower()))
    user = res.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if user.status != "Active":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account inactive")
    user.last_login_at = datetime.utcnow()
    await db.commit()
    token = create_access_token(user.id, extra={"role": user.role, "email": user.email})
    rate_limit_clear_login(request)
    await write_audit(db, user_id=user.id, user_email=user.email, action="login", entity_type="user", entity_id=user.id,
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
    return Token(access_token=token, force_password_reset=user.force_password_reset, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.post("/reset-password", response_model=UserOut)
async def reset_password(body: PasswordResetRequest, request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.password_hash or not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password incorrect")
    if len(body.new_password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must be at least 8 characters")
    user.password_hash = hash_password(body.new_password)
    user.force_password_reset = False
    user.updated_at = datetime.utcnow()
    await db.commit()
    await write_audit(db, user_id=user.id, user_email=user.email, action="reset_password", entity_type="user", entity_id=user.id,
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
    return UserOut.model_validate(user)


@router.get("/google/status")
async def google_status():
    client_id = await get_setting("google_oauth_client_id")
    redirect_uri = await get_setting("google_oauth_redirect_uri")
    configured = bool(client_id)
    return {"configured": configured, "client_id_preview": (client_id[:6] + "…") if client_id else None, "redirect_uri": redirect_uri}


@router.get("/google/start")
async def google_start():
    client_id = await get_setting("google_oauth_client_id")
    redirect_uri = await get_setting("google_oauth_redirect_uri")
    if not client_id or not redirect_uri:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Google OAuth not configured by admin yet")
    from urllib.parse import urlencode
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
    }
    return {"url": f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"}
