from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.follows import FollowRepository
from app.repositories.outbox import OutboxRepository
from app.repositories.users import UserRepository
from app.utils.exceptions import ConflictError, NotFoundError


class FollowService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.follows = FollowRepository(session)
        self.users = UserRepository(session)
        self.outbox = OutboxRepository(session)

    async def follow(self, follower_id: str, followed_id: str):
        if follower_id == followed_id:
            raise ConflictError("Cannot follow self")
        if not await self.users.get(followed_id):
            raise NotFoundError("User not found")
        if await self.follows.exists(follower_id, followed_id):
            raise ConflictError("Already following")
        await self.follows.create(follower_id, followed_id)
        await self.outbox.enqueue(
            topic="user.followed",
            event_type="user.followed",
            payload={
                "event_id": str(uuid.uuid4()),
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "follower_id": follower_id,
                "followed_id": followed_id,
            },
        )
        await self.session.commit()

    async def unfollow(self, follower_id: str, followed_id: str):
        await self.follows.delete(follower_id, followed_id)
        await self.session.commit()

    async def list_followers(self, user_id: str, page: int, size: int):
        limit = size
        offset = (page - 1) * size
        return await self.follows.list_followers(user_id, limit, offset)

    async def list_following(self, user_id: str, page: int, size: int):
        limit = size
        offset = (page - 1) * size
        return await self.follows.list_following(user_id, limit, offset)
