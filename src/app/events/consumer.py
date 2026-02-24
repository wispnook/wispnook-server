from __future__ import annotations

import asyncio
import json
from typing import Any, cast

from aiokafka import AIOKafkaConsumer
from redis.asyncio import Redis

from app.cache.redis_client import redis_client
from app.config.settings import settings
from app.domain.events.schemas import (
    EVENT_TOPIC_MAP,
    CommentCreatedEvent,
    PostCreatedEvent,
    PostLikedEvent,
    UserFollowedEvent,
)
from app.observability.logging import get_logger

logger = get_logger(__name__)


class KafkaEventConsumer:
    def __init__(self) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._consumer:
            return
        self._consumer = AIOKafkaConsumer(
            *settings.kafka_topic_list,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_group_id,
            client_id=f"{settings.kafka_client_id}-consumer",
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        await self._consumer.start()
        self._stop_event.clear()
        self._task = asyncio.create_task(self._consume_loop())
        logger.info("Kafka consumer started")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            await self._task
        if self._consumer:
            await self._consumer.stop()
            logger.info("Kafka consumer stopped")
            self._consumer = None

    async def _consume_loop(self) -> None:
        assert self._consumer is not None
        redis = await redis_client.get_client()
        async for message in self._consumer:
            if self._stop_event.is_set():
                break
            topic = message.topic
            payload = message.value
            await self._handle_message(redis, topic, payload)

    async def _handle_message(self, redis: Redis, topic: str, payload: dict[str, Any]) -> None:
        schema = EVENT_TOPIC_MAP.get(topic)
        if not schema:
            logger.warning("Unknown event topic", topic=topic)
            return
        event = schema.model_validate(payload)
        event_key = f"events:{event.event_id}"
        if await redis.get(event_key):
            logger.debug("Event already processed", event_id=str(event.event_id))
            return
        if topic == "post.liked":
            liked_event = cast(PostLikedEvent, event)
            await redis.hincrby("post:like_counts", str(liked_event.post_id), 1)
        elif topic == "user.followed":
            followed_event = cast(UserFollowedEvent, event)
            await redis.hincrby("user:followers", str(followed_event.followed_id), 1)
        elif topic == "post.created":
            post_created = cast(PostCreatedEvent, event)
            post_data = post_created.post.model_dump()
            await redis.lpush(f"feed:{post_data['author_id']}", json.dumps(post_data))
            await redis.ltrim(f"feed:{post_data['author_id']}", 0, 99)
        elif topic == "comment.created":
            comment_event = cast(CommentCreatedEvent, event)
            await redis.hincrby("post:comment_counts", str(comment_event.comment.post_id), 1)
        await redis.set(event_key, "1", ex=settings.idempotency_ttl_seconds)
        logger.debug("Processed event", topic=topic, event_id=str(event.event_id))


consumer = KafkaEventConsumer()
