from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.common import get_current_user, get_redis, get_session
from app.domain.schemas.feed import FeedResponse
from app.domain.schemas.posts import PostOut
from app.services.feed_service import FeedService

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get(
    "",
    response_model=FeedResponse,
    summary="Get timeline feed",
    description=(
        "Returns a paginated list of posts from users the authenticated user follows, "
        "ordered by recency. Results are cached per user for 60 seconds."
    ),
    response_description="Paginated feed of posts from followed users",
)
async def get_feed(
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
    session: AsyncSession = Depends(get_session),
    redis=Depends(get_redis),
    user=Depends(get_current_user),
):
    service = FeedService(session)
    raw_items = await service.get_feed(str(user.id), page, size, redis)
    posts = [
        PostOut.model_validate({**item, "like_count": item.get("like_count", 0) or 0})
        for item in raw_items
    ]
    return FeedResponse(items=posts, page=page, size=size)
