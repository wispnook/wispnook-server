from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, model, entity_id):
        stmt = select(model).where(model.id == entity_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
