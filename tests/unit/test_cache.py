import pytest

from app.cache.redis_client import redis_client


class DummyRedis:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_redis_client_lifecycle(monkeypatch):
    dummy = DummyRedis()

    def fake_from_url(url, decode_responses=True):  # noqa: ARG001
        return dummy

    monkeypatch.setattr("app.cache.redis_client.aioredis.from_url", fake_from_url)

    client = redis_client.init()
    assert client is dummy

    cached_client = await redis_client.get_client()
    assert cached_client is dummy

    await redis_client.close()
    assert dummy.closed
