from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.comments import CommentCreate
from app.repositories.comments import CommentRepository
from app.repositories.outbox import OutboxRepository
from app.repositories.posts import PostRepository
from app.utils.exceptions import NotFoundError, UnauthorizedError


class CommentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.comments = CommentRepository(session)
        self.posts = PostRepository(session)
        self.outbox = OutboxRepository(session)

    async def add_comment(self, post_id: str, author_id: str, payload: CommentCreate):
        if not await self.posts.get(post_id):
            raise NotFoundError("Post not found")
        comment = await self.comments.create(
            post_id=post_id,
            author_id=author_id,
            content=payload.content,
        )
        await self.outbox.enqueue(
            topic="comment.created",
            event_type="comment.created",
            payload={
                "event_id": str(comment.id),
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "comment": {
                    "id": str(comment.id),
                    "post_id": str(comment.post_id),
                    "author_id": str(comment.author_id),
                    "content": comment.content,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                },
            },
        )
        await self.session.commit()
        return comment

    async def list_comments(self, post_id: str, page: int, size: int):
        limit = size
        offset = (page - 1) * size
        return await self.comments.list_for_post(post_id, limit, offset)

    async def delete_comment(self, comment_id: str, user_id: str, is_admin: bool):
        comment = await self.comments.get(comment_id)
        if not comment:
            raise NotFoundError("Comment not found")
        if str(comment.author_id) != user_id and not is_admin:
            raise UnauthorizedError("Cannot delete comment")
        await self.comments.delete(comment)
        await self.session.commit()
