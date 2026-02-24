from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostCreate(BaseModel):
    content: str = Field(min_length=1, max_length=280)
    media_url: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=64)


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    author_id: uuid.UUID
    content: str
    media_url: str | None
    created_at: datetime
    updated_at: datetime
    like_count: int = 0


class PostListResponse(BaseModel):
    items: list[PostOut]
    page: int
    size: int
    total: int
