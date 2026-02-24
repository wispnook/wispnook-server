from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import Like, Post


def _as_uuid(value: uuid.UUID | str) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(value)


class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **kwargs) -> Post:
        kwargs["author_id"] = _as_uuid(kwargs["author_id"])
        post = Post(**kwargs)
        self.session.add(post)
        await self.session.flush()
        return post

    async def get(self, post_id: uuid.UUID | str):
        stmt = select(Post).where(Post.id == _as_uuid(post_id))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list(self, author_id: str | None, limit: int, offset: int) -> tuple[list[Post], int]:
        stmt: Select[tuple[Post]] = select(Post)
        count_stmt = select(func.count()).select_from(Post)
        if author_id:
            author_uuid = _as_uuid(author_id)
            stmt = stmt.where(Post.author_id == author_uuid)
            count_stmt = count_stmt.where(Post.author_id == author_uuid)
        stmt = stmt.order_by(Post.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        total = await self.session.scalar(count_stmt)
        return list(items), int(total or 0)

    async def delete(self, post: Post) -> None:
        await self.session.delete(post)

    async def count_likes(self, post_id: uuid.UUID | str) -> int:
        stmt = select(func.count()).where(Like.post_id == _as_uuid(post_id))
        return int(await self.session.scalar(stmt) or 0)

    async def list_feed(self, user_ids: Sequence[str], limit: int, offset: int):
        uuid_ids = [_as_uuid(user_id) for user_id in user_ids]
        stmt = (
            select(Post)
            .where(Post.author_id.in_(uuid_ids))
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
