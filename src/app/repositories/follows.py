from __future__ import annotations

import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import Follow


def _as_uuid(value: uuid.UUID | str) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(value)


class FollowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, follower_id, followed_id) -> Follow:
        follow = Follow(follower_id=_as_uuid(follower_id), followed_id=_as_uuid(followed_id))
        self.session.add(follow)
        await self.session.flush()
        return follow

    async def delete(self, follower_id, followed_id) -> None:
        stmt = select(Follow).where(
            Follow.follower_id == _as_uuid(follower_id), Follow.followed_id == _as_uuid(followed_id)
        )
        result = await self.session.execute(stmt)
        follow = result.scalar_one_or_none()
        if follow:
            await self.session.delete(follow)

    async def list_followers(self, user_id: str, limit: int, offset: int):
        stmt: Select[tuple[Follow]] = (
            select(Follow)
            .where(Follow.followed_id == _as_uuid(user_id))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        count_stmt = select(func.count()).where(Follow.followed_id == _as_uuid(user_id))
        total = await self.session.scalar(count_stmt)
        return items, int(total or 0)

    async def list_following(self, user_id: str, limit: int, offset: int):
        stmt = (
            select(Follow)
            .where(Follow.follower_id == _as_uuid(user_id))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        count_stmt = select(func.count()).where(Follow.follower_id == _as_uuid(user_id))
        total = await self.session.scalar(count_stmt)
        return items, int(total or 0)

    async def exists(self, follower_id, followed_id) -> bool:
        stmt = select(Follow).where(
            Follow.follower_id == _as_uuid(follower_id), Follow.followed_id == _as_uuid(followed_id)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None
