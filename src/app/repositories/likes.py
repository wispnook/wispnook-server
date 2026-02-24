from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import Like


def _as_uuid(value: uuid.UUID | str) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(value)


class LikeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, post_id, user_id) -> Like:
        like = Like(post_id=_as_uuid(post_id), user_id=_as_uuid(user_id))
        self.session.add(like)
        await self.session.flush()
        return like

    async def delete(self, post_id, user_id) -> None:
        stmt = select(Like).where(
            Like.post_id == _as_uuid(post_id), Like.user_id == _as_uuid(user_id)
        )
        result = await self.session.execute(stmt)
        like = result.scalar_one_or_none()
        if like:
            await self.session.delete(like)

    async def exists(self, post_id, user_id) -> bool:
        stmt = select(Like).where(
            Like.post_id == _as_uuid(post_id), Like.user_id == _as_uuid(user_id)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None

    async def count(self, post_id) -> int:
        stmt = select(func.count()).where(Like.post_id == _as_uuid(post_id))
        return int(await self.session.scalar(stmt) or 0)
