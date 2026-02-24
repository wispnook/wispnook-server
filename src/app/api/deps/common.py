from __future__ import annotations

from uuid import UUID

from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer

from app.auth.security import decode_token
from app.cache.redis_client import redis_dependency
from app.db.session import get_session
from app.repositories.users import UserRepository
from app.utils.exceptions import NotFoundError, UnauthorizedError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Security(oauth2_scheme), session=Depends(get_session)):
    try:
        payload = decode_token(token)
    except ValueError as exc:  # pragma: no cover - security
        raise UnauthorizedError("Invalid token") from exc
    user_id = payload.get("sub")
    users = UserRepository(session)
    user = await users.get(UUID(user_id))
    if not user:
        raise NotFoundError("User not found")
    return user


async def get_current_admin(user=Depends(get_current_user)):
    if user.role != "admin":
        raise UnauthorizedError("Admin privileges required")
    return user


get_redis = redis_dependency
