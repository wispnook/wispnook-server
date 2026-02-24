from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.domain.schemas.posts import PostOut


class FeedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[PostOut]
    page: int
    size: int
