import pytest
from fastapi import Request

from app.rate_limit.dependency import rate_limiter
from app.utils.exceptions import RateLimitError


class FakePipeline:
    def __init__(self, store, key):
        self.store = store
        self.key = key
        self.ops = []

    def incr(self, key, amount):
        self.ops.append(("incr", key, amount))
        return self

    def expire(self, key, ttl):
        self.ops.append(("expire", key, ttl))
        return self

    async def execute(self):
        for op in self.ops:
            if op[0] == "incr":
                self.store[op[1]] = self.store.get(op[1], 0) + op[2]
            elif op[0] == "expire":
                pass
        self.ops = []


class FakeRedis:
    def __init__(self):
        self.store: dict[str, int] = {}

    async def ttl(self, key):
        return -1

    async def get(self, key):
        value = self.store.get(key)
        return str(value) if value is not None else None

    def pipeline(self):
        return FakePipeline(self.store, "")


@pytest.mark.asyncio
async def test_rate_limiter_blocks_after_threshold():
    redis = FakeRedis()
    scope = {"client": ("127.0.0.1", 1234), "type": "http"}
    request = Request(scope)

    await rate_limiter(request=request, redis=redis, requests_per_window=1, window_seconds=60)
    with pytest.raises(RateLimitError):
        await rate_limiter(request=request, redis=redis, requests_per_window=1, window_seconds=60)
