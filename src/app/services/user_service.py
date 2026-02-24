from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_password
from app.domain.schemas.users import UserUpdate
from app.repositories.users import UserRepository
from app.utils.exceptions import NotFoundError


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def me(self, user_id: str):
        user = await self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    async def update_profile(self, user_id: str, payload: UserUpdate):
        user = await self.me(user_id)
        updated = await self.users.update(
            user,
            email=payload.email,
            bio=payload.bio,
            username=payload.username,
            password_hash=hash_password(payload.password) if payload.password else None,
        )
        await self.session.commit()
        return updated

    async def search(self, query: str | None, page: int, size: int):
        limit = size
        offset = (page - 1) * size
        items, total = await self.users.list(query, limit, offset)
        return items, total
