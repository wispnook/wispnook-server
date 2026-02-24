from __future__ import annotations

from collections.abc import AsyncIterator

import redis.asyncio as aioredis

from app.config.settings import settings


class RedisClient:
    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    def init(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(str(settings.redis_url), decode_responses=True)
        return self._client

    async def get_client(self) -> aioredis.Redis:
        if self._client is None:
            self.init()
        assert self._client is not None
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None


redis_client = RedisClient()


async def redis_dependency() -> AsyncIterator[aioredis.Redis]:
    client = await redis_client.get_client()
    yield client
