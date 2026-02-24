from __future__ import annotations

import asyncio
import json

from app.config.settings import settings
from app.events.producer import producer
from app.observability.logging import get_logger
from app.repositories.outbox import OutboxRepository

logger = get_logger(__name__)


class OutboxDispatcher:
    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run())
        logger.info("Outbox dispatcher started")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            await self._task
        logger.info("Outbox dispatcher stopped")

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            async with self._session_factory() as session:
                repo = OutboxRepository(session)
                entries = await repo.pending(limit=50)
                for entry in entries:
                    payload = json.loads(entry.payload)
                    await producer.publish(entry.topic, payload)
                    await repo.mark_published(entry)
                await session.commit()
            await asyncio.sleep(settings.outbox_dispatch_interval_seconds)


def create_dispatcher(session_factory) -> OutboxDispatcher:
    return OutboxDispatcher(session_factory)
