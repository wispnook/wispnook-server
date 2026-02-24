from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list(self, query: str | None, limit: int, offset: int) -> tuple[Sequence[User], int]:
        stmt: Select[tuple[User]] = select(User)
        count_stmt = select(func.count()).select_from(User)
        if query:
            stmt = stmt.where(User.username.ilike(f"%{query}%"))
            count_stmt = count_stmt.where(User.username.ilike(f"%{query}%"))
        stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        total = await self.session.scalar(count_stmt)
        return items, int(total or 0)

    async def get(self, user_id: uuid.UUID | str):
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        stmt = select(User).where(User.id == user_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if value is not None:
                setattr(user, key, value)
        await self.session.flush()
        return user
