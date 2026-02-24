from __future__ import annotations

import uuid
from datetime import datetime, timezone

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.posts import PostCreate
from app.repositories.likes import LikeRepository
from app.repositories.outbox import OutboxRepository
from app.repositories.posts import PostRepository
from app.utils.exceptions import ConflictError, NotFoundError, UnauthorizedError


class PostService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.posts = PostRepository(session)
        self.likes = LikeRepository(session)
        self.outbox = OutboxRepository(session)

    async def create_post(self, user_id: str, payload: PostCreate, redis: aioredis.Redis):
        if payload.idempotency_key:
            cache_key = f"idempotency:post:{payload.idempotency_key}:{user_id}"
            existing_id = await redis.get(cache_key)
            if existing_id:
                existing = await self.posts.get(existing_id)
                if existing:
                    return existing
        post = await self.posts.create(
            author_id=user_id,
            content=payload.content,
            media_url=payload.media_url,
        )
        event_payload = {
            "event_id": str(post.id),
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "post": {
                "id": str(post.id),
                "author_id": str(post.author_id),
                "content": post.content,
                "media_url": post.media_url,
                "created_at": post.created_at.isoformat() if post.created_at else None,
            },
        }
        await self.outbox.enqueue(
            topic="post.created", payload=event_payload, event_type="post.created"
        )
        await self.session.commit()
        if payload.idempotency_key:
            await redis.set(cache_key, str(post.id), ex=3600)
        return post

    async def get_post(self, post_id: str):
        post = await self.posts.get(post_id)
        if not post:
            raise NotFoundError("Post not found")
        return post

    async def list_posts(self, page: int, size: int, author_id: str | None):
        limit = size
        offset = (page - 1) * size
        items, total = await self.posts.list(author_id, limit, offset)
        return items, total

    async def delete_post(self, post_id: str, current_user_id: str, is_admin: bool):
        post = await self.posts.get(post_id)
        if not post:
            raise NotFoundError("Post not found")
        if str(post.author_id) != current_user_id and not is_admin:
            raise UnauthorizedError("Cannot delete post")
        await self.posts.delete(post)
        await self.session.commit()

    async def like_post(self, post_id: str, user_id: str, redis: aioredis.Redis):
        if await self.likes.exists(post_id, user_id):
            raise ConflictError("Already liked")
        await self.likes.create(post_id, user_id)
        await redis.hincrby("post:like_counts", post_id, 1)
        event_payload = {
            "event_id": str(uuid.uuid4()),
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "post_id": post_id,
            "user_id": user_id,
        }
        await self.outbox.enqueue(
            topic="post.liked", payload=event_payload, event_type="post.liked"
        )
        await self.session.commit()

    async def unlike_post(self, post_id: str, user_id: str, redis: aioredis.Redis):
        if not await self.likes.exists(post_id, user_id):
            return
        await self.likes.delete(post_id, user_id)
        new_count = await redis.hincrby("post:like_counts", post_id, -1)
        if new_count < 0:
            await redis.hset("post:like_counts", post_id, 0)
        await self.session.commit()

    async def count_likes(self, post_id: str, redis: aioredis.Redis) -> int:
        cached = await redis.hget("post:like_counts", post_id)
        if cached is not None:
            return int(cached)
        count = await self.likes.count(post_id)
        await redis.hset("post:like_counts", post_id, count)
        return count
