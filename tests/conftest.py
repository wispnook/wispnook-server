from collections import defaultdict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps.common import get_redis, get_session
from app.cache.redis_client import redis_client
from app.db.session import Base
from app.main import consumer, create_app, dispatcher, producer


class FakeAsyncComponent:
    async def start(self):
        return None

    async def stop(self):
        return None


class InMemoryRedis:
    def __init__(self):
        self.store = defaultdict(int)
        self.hash_store = defaultdict(dict)

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = value

    async def ttl(self, key):
        return -1

    def pipeline(self):
        return self

    def incr(self, key, amount):
        self.store[key] = int(self.store.get(key, 0)) + amount
        return self

    def expire(self, key, ttl):
        return self

    async def execute(self):
        return None

    async def hincrby(self, name, key, amount):
        self.hash_store[name][key] = int(self.hash_store[name].get(key, 0)) + amount
        return self.hash_store[name][key]

    async def hget(self, name, key):
        return self.hash_store[name].get(key)

    async def hset(self, name, key, value):
        self.hash_store[name][key] = value

    async def close(self):
        return None


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DB_URL)
TestSession = async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(producer, "start", FakeAsyncComponent().start)
    monkeypatch.setattr(producer, "stop", FakeAsyncComponent().stop)
    monkeypatch.setattr(consumer, "start", FakeAsyncComponent().start)
    monkeypatch.setattr(consumer, "stop", FakeAsyncComponent().stop)
    monkeypatch.setattr(dispatcher, "start", FakeAsyncComponent().start)
    monkeypatch.setattr(dispatcher, "stop", FakeAsyncComponent().stop)

    fake_redis = InMemoryRedis()

    async def _override_session():  # type: ignore[override]
        async with TestSession() as session:
            yield session

    async def _override_redis():
        return fake_redis

    monkeypatch.setattr(redis_client, "init", lambda: None)
    monkeypatch.setattr(redis_client, "close", fake_redis.close)

    async def _get_client():
        return fake_redis

    monkeypatch.setattr(redis_client, "get_client", _get_client)

    application = create_app()
    application.dependency_overrides[get_session] = _override_session
    application.dependency_overrides[get_redis] = _override_redis
    return application


@pytest.fixture
def client(app):
    return TestClient(app)
