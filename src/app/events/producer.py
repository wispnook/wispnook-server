from __future__ import annotations

import asyncio
import json

from aiokafka import AIOKafkaProducer

from app.config.settings import settings
from app.observability.logging import get_logger

logger = get_logger(__name__)


class KafkaEventProducer:
    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._producer is None:
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=settings.kafka_bootstrap_servers,
                    client_id=settings.kafka_client_id,
                    security_protocol=settings.kafka_security_protocol,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                )
                await self._producer.start()
                logger.info("Kafka producer started")

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer stopped")
            self._producer = None

    async def publish(self, topic: str, payload: dict) -> None:
        if self._producer is None:
            await self.start()
        assert self._producer is not None
        await self._producer.send_and_wait(topic, payload)
        logger.debug("Published event", topic=topic)


producer = KafkaEventProducer()
