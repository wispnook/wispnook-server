from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import EventOutbox


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def enqueue(self, topic: str, payload: dict, event_type: str) -> EventOutbox:
        entry = EventOutbox(topic=topic, payload=json.dumps(payload), event_type=event_type)
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def pending(self, limit: int = 100):
        stmt = select(EventOutbox).where(EventOutbox.published.is_(False)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_published(self, entry: EventOutbox) -> None:
        entry.published = True
        await self.session.flush()
