"""Security helpers: password hashing, JWT, RBAC."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = settings.jwt_algorithm


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return cast(str, jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM))


def create_refresh_token(subject: str | Any) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return cast(str, jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM))


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return cast(dict[str, Any] | None, payload)
    except JWTError:
        return None


def generate_temporary_password_reset_token() -> str:
    import secrets

    return secrets.token_urlsafe(32)
