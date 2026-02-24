from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain.schemas.auth import TokenPair
from app.repositories.outbox import OutboxRepository
from app.repositories.users import UserRepository
from app.utils.exceptions import ConflictError, UnauthorizedError


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.outbox = OutboxRepository(session)

    async def register_user(
        self, email: str, username: str, password: str, bio: str | None
    ) -> TokenPair:
        if await self.users.get_by_email(email) or await self.users.get_by_username(username):
            raise ConflictError("User already exists")
        user = await self.users.create(
            email=email,
            username=username,
            password_hash=hash_password(password),
            bio=bio,
        )
        occurred_at = datetime.now(timezone.utc).isoformat()
        await self.outbox.enqueue(
            topic="user.created",
            event_type="user.created",
            payload={
                "event_id": str(user.id),
                "occurred_at": occurred_at,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                },
            },
        )
        await self.session.commit()
        access_token, expires_at = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        return TokenPair(
            access_token=access_token, refresh_token=refresh_token, expires_at=expires_at
        )

    async def login(self, username: str, password: str) -> TokenPair:
        user = await self.users.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid credentials")
        access_token, expires_at = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        return TokenPair(
            access_token=access_token, refresh_token=refresh_token, expires_at=expires_at
        )

    async def rotate_refresh_token(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token)
        except ValueError as exc:  # pragma: no cover - handled via tests
            raise UnauthorizedError("Invalid refresh token") from exc
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")
        user_id = payload.get("sub")
        user = await self.users.get(UUID(user_id))
        if not user:
            raise UnauthorizedError("User no longer exists")
        access_token, expires_at = create_access_token(str(user.id))
        new_refresh = create_refresh_token(str(user.id))
        return TokenPair(
            access_token=access_token, refresh_token=new_refresh, expires_at=expires_at
        )
