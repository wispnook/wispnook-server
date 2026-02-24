from collections import defaultdict

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.session import Base
from app.domain.schemas.posts import PostCreate
from app.repositories.users import UserRepository
from app.services.auth_service import AuthService
from app.services.feed_service import FeedService
from app.services.follow_service import FollowService
from app.services.post_service import PostService
from app.utils.exceptions import ConflictError


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


async def _create_user(session, email: str, username: str):
    auth = AuthService(session)
    await auth.register_user(email=email, username=username, password="Password123!", bio=None)
    repo = UserRepository(session)
    return await repo.get_by_username(username)


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.hash_store: dict[str, dict[str, int]] = defaultdict(dict)

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):  # noqa: ARG002
        self.store[key] = value

    async def hincrby(self, name: str, key: str, amount: int):
        self.hash_store[name][key] = int(self.hash_store[name].get(key, 0)) + amount
        return self.hash_store[name][key]

    async def hget(self, name: str, key: str):
        value = self.hash_store[name].get(key)
        return str(value) if value is not None else None

    async def hset(self, name: str, key: str, value: int):
        self.hash_store[name][key] = value


@pytest.mark.asyncio
async def test_follow_service_flow(session):
    follower = await _create_user(session, "alpha@example.com", "alpha")
    followed = await _create_user(session, "beta@example.com", "beta")
    service = FollowService(session)

    await service.follow(str(follower.id), str(followed.id))
    items, total = await service.list_followers(str(followed.id), page=1, size=10)
    assert total == 1
    assert items[0].follower_id == follower.id

    await service.unfollow(str(follower.id), str(followed.id))
    items, total = await service.list_followers(str(followed.id), page=1, size=10)
    assert total == 0
    assert items == []


@pytest.mark.asyncio
async def test_follow_service_prevents_self_follow(session):
    user = await _create_user(session, "self@example.com", "self")
    service = FollowService(session)
    with pytest.raises(ConflictError):
        await service.follow(str(user.id), str(user.id))


@pytest.mark.asyncio
async def test_post_service_like_flow(session):
    user = await _create_user(session, "gamma@example.com", "gamma")
    service = PostService(session)
    redis = FakeRedis()

    post = await service.create_post(str(user.id), PostCreate(content="hello world"), redis)
    assert post.content == "hello world"
    assert await service.count_likes(str(post.id), redis) == 0

    await service.like_post(str(post.id), str(user.id), redis)
    assert await service.count_likes(str(post.id), redis) == 1

    await service.unlike_post(str(post.id), str(user.id), redis)
    assert await service.count_likes(str(post.id), redis) == 0


@pytest.mark.asyncio
async def test_feed_service_returns_cached_posts(session):
    follower = await _create_user(session, "delta@example.com", "delta")
    followed = await _create_user(session, "epsilon@example.com", "epsilon")
    follow_service = FollowService(session)
    await follow_service.follow(str(follower.id), str(followed.id))

    post_service = PostService(session)
    redis = FakeRedis()
    await post_service.create_post(str(followed.id), PostCreate(content="feed post"), redis)

    feed_service = FeedService(session)
    items = await feed_service.get_feed(str(follower.id), page=1, size=10, redis=redis)
    assert any(item["content"] == "feed post" for item in items)
    cached_items = await feed_service.get_feed(str(follower.id), page=1, size=10, redis=redis)
    assert cached_items == items


@pytest.mark.asyncio
async def test_auth_service_refresh_token(session):
    auth = AuthService(session)
    await auth.register_user("zeta@example.com", "zeta", "Password123!", None)
    user_repo = UserRepository(session)
    user = await user_repo.get_by_username("zeta")

    tokens = await auth.login("zeta", "Password123!")
    rotated = await auth.rotate_refresh_token(tokens.refresh_token)
    assert rotated.access_token != tokens.access_token
    assert rotated.refresh_token != tokens.refresh_token
    # ensure original user still resolvable
    assert user.email == "zeta@example.com"
