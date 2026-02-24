from __future__ import annotations

import json

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.follows import FollowRepository
from app.repositories.posts import PostRepository

FEED_TTL_SECONDS = 60


class FeedService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.posts = PostRepository(session)
        self.follows = FollowRepository(session)

    async def get_feed(self, user_id: str, page: int, size: int, redis: aioredis.Redis):
        cache_key = f"feed:{user_id}:{page}:{size}"
        cached = await redis.get(cache_key)
        if cached:
            items = json.loads(cached)
            return items
        follows, _ = await self.follows.list_following(user_id, 1000, 0)
        author_ids = [follow.followed_id for follow in follows] or [user_id]
        offset = (page - 1) * size
        posts = await self.posts.list_feed(author_ids, size, offset)
        items = [
            {
                "id": str(post.id),
                "author_id": str(post.author_id),
                "content": post.content,
                "media_url": post.media_url,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "updated_at": post.updated_at.isoformat() if post.updated_at else None,
                "like_count": 0,
            }
            for post in posts
        ]
        await redis.set(cache_key, json.dumps(items), ex=FEED_TTL_SECONDS)
        return items
