from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.common import get_current_user, get_session
from app.rate_limit.dependency import rate_limiter
from app.services.comment_service import CommentService

router = APIRouter(prefix="/comments", tags=["comments"])


@router.delete(
    "/{comment_id}",
    status_code=204,
    dependencies=[Depends(rate_limiter)],
    summary="Delete a comment",
    description=(
        "Permanently delete a comment. "
        "Only the comment's author or an admin can perform this action."
    ),
)
async def delete_comment(
    comment_id: str,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    service = CommentService(session)
    await service.delete_comment(comment_id, str(user.id), user.role == "admin")
