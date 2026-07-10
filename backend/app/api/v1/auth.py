"""Authentication routes."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.models.models import PasswordReset, User, UserProfile
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenOut,
    UserCreate,
    UserLogin,
    UserOut,
    UserUpdate,
)

router = APIRouter(tags=["Auth"])


def _user_out(user: User) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    stmt = select(User).where(User.email == payload.email)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role="candidate",
    )
    db.add(user)
    await db.flush()
    db.add(UserProfile(user_id=user.id))
    await db.commit()

    result = await db.execute(
        select(User).options(selectinload(User.profile)).where(User.id == user.id)
    )
    user = result.scalar_one()

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "user": _user_out(user)}


@router.post("/login", response_model=TokenOut)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(User).options(selectinload(User.profile)).where(User.email == form_data.username)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "user": _user_out(user)}


@router.post("/login/json", response_model=TokenOut)
async def login_json(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    stmt = select(User).options(selectinload(User.profile)).where(User.email == payload.email)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "user": _user_out(user)}


@router.post("/refresh", response_model=TokenOut)
async def refresh(token: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    from uuid import UUID

    user_id = UUID(payload["sub"])
    user = (
        await db.execute(
            select(User).options(selectinload(User.profile)).where(User.id == user_id)
        )
    ).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "user": _user_out(user)}


@router.post("/password-reset/request")
async def request_password_reset(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    from hashlib import sha256

    from app.core.security import generate_temporary_password_reset_token

    stmt = select(User).where(User.email == payload.email)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        return {"message": "If the email exists, a reset link has been sent."}

    raw_token = generate_temporary_password_reset_token()
    token_hash = sha256(raw_token.encode()).hexdigest()
    reset = PasswordReset(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    db.add(reset)
    await db.commit()

    # In production, send email with raw_token here.
    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    from hashlib import sha256

    token_hash = sha256(payload.token.encode()).hexdigest()
    stmt = select(PasswordReset).where(
        PasswordReset.token_hash == token_hash,
        PasswordReset.used.is_(False),
        PasswordReset.expires_at > datetime.now(UTC),
    )
    reset = (await db.execute(stmt)).scalar_one_or_none()
    if not reset:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = (await db.execute(select(User).where(User.id == reset.user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.hashed_password = get_password_hash(payload.new_password)
    reset.used = True
    await db.commit()
    return {"message": "Password updated successfully."}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return _user_out(user)


@router.put("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if user.profile:
        for field in ["phone", "location", "linkedin_url", "portfolio_url", "bio"]:
            value = getattr(payload, field, None)
            if value is not None:
                setattr(user.profile, field, value)
    await db.commit()
    result = await db.execute(
        select(User).options(selectinload(User.profile)).where(User.id == user.id)
    )
    user = result.scalar_one()
    return _user_out(user)


@router.post("/google")
async def google_login(token: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Verify a Google ID token and create/login user."""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": token},
            )
            resp.raise_for_status()
            info = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid Google token") from exc

    if info.get("aud") != settings.google_client_id:
        raise HTTPException(status_code=401, detail="Invalid Google token audience")

    email = info.get("email")
    provider_id = info.get("sub")
    name = info.get("name")

    stmt = select(User).options(selectinload(User.profile)).where(User.email == email)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        user = User(
            email=email,
            full_name=name,
            auth_provider="google",
            provider_id=provider_id,
            is_verified=True,
        )
        db.add(user)
        await db.flush()
        db.add(UserProfile(user_id=user.id))
        await db.commit()

        result = await db.execute(
            select(User).options(selectinload(User.profile)).where(User.id == user.id)
        )
        user = result.scalar_one()

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "user": _user_out(user)}
