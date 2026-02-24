from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import Comment


def _as_uuid(value: uuid.UUID | str) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(value)


class CommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **kwargs) -> Comment:
        kwargs["post_id"] = _as_uuid(kwargs["post_id"])
        kwargs["author_id"] = _as_uuid(kwargs["author_id"])
        comment = Comment(**kwargs)
        self.session.add(comment)
        await self.session.flush()
        return comment

    async def list_for_post(self, post_id, limit: int, offset: int):
        stmt = (
            select(Comment)
            .where(Comment.post_id == _as_uuid(post_id))
            .order_by(Comment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        count_stmt = select(func.count()).where(Comment.post_id == _as_uuid(post_id))
        total = await self.session.scalar(count_stmt)
        return items, int(total or 0)

    async def get(self, comment_id):
        stmt = select(Comment).where(Comment.id == _as_uuid(comment_id))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def delete(self, comment: Comment) -> None:
        await self.session.delete(comment)
