from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EventMetadata(BaseModel):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    occurred_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreatedPayload(BaseModel):
    id: uuid.UUID
    email: str
    username: str


class UserCreatedEvent(EventMetadata):
    user: UserCreatedPayload


class UserFollowedEvent(EventMetadata):
    follower_id: uuid.UUID
    followed_id: uuid.UUID


class PostCreatedPayload(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    content: str
    media_url: str | None
    created_at: datetime


class PostCreatedEvent(EventMetadata):
    post: PostCreatedPayload


class PostLikedEvent(EventMetadata):
    post_id: uuid.UUID
    user_id: uuid.UUID


class CommentCreatedPayload(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    author_id: uuid.UUID
    content: str
    created_at: datetime


class CommentCreatedEvent(EventMetadata):
    comment: CommentCreatedPayload


EVENT_TOPIC_MAP: dict[str, type[EventMetadata]] = {
    "user.created": UserCreatedEvent,
    "user.followed": UserFollowedEvent,
    "post.created": PostCreatedEvent,
    "post.liked": PostLikedEvent,
    "comment.created": CommentCreatedEvent,
}
