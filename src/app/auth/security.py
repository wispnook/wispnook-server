from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def _create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "exp": now + expires_delta,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": token_type,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_access_token(subject: str) -> tuple[str, datetime]:
    expires_delta = timedelta(minutes=settings.jwt_exp_minutes)
    expiration = datetime.now(timezone.utc) + expires_delta
    return _create_token(subject, expires_delta, "access"), expiration


def create_refresh_token(subject: str) -> str:
    expires_delta = timedelta(minutes=settings.jwt_refresh_exp_minutes)
    return _create_token(subject, expires_delta, "refresh")


def decode_token(token: str) -> dict[str, str]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except JWTError as exc:  # pragma: no cover - jose raises many subclasses
        raise ValueError("Invalid token") from exc
