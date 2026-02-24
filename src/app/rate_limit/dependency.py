from __future__ import annotations

from fastapi import Depends, Request

from app.cache.redis_client import redis_dependency
from app.config.settings import settings
from app.utils.exceptions import RateLimitError


async def rate_limiter(
    request: Request,
    redis=Depends(redis_dependency),
    requests_per_window: int = settings.rate_limit_requests,
    window_seconds: int = settings.rate_limit_window_seconds,
) -> None:
    identifier = request.client.host if request.client else "anon"
    path = request.scope.get("path", "/")
    key = f"rate:{identifier}:{path}"
    ttl = await redis.ttl(key)
    current = await redis.get(key)
    count = int(current) if current else 0
    if count >= requests_per_window:
        raise RateLimitError("Too many requests")
    pipe = redis.pipeline()
    pipe.incr(key, 1)
    if ttl == -1:
        pipe.expire(key, window_seconds)
    await pipe.execute()
