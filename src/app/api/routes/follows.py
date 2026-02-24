from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.common import get_current_user, get_session
from app.rate_limit.dependency import rate_limiter
from app.services.follow_service import FollowService

router = APIRouter(prefix="/follows", tags=["follows"])


@router.post(
    "/{user_id}",
    status_code=204,
    dependencies=[Depends(rate_limiter)],
    summary="Follow a user",
    description="Start following another user. Following yourself or a user you already follow has no effect.",
)
async def follow_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    service = FollowService(session)
    await service.follow(str(user.id), user_id)


@router.delete(
    "/{user_id}",
    status_code=204,
    dependencies=[Depends(rate_limiter)],
    summary="Unfollow a user",
    description="Stop following a user. Unfollowing someone you don't follow has no effect.",
)
async def unfollow_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    service = FollowService(session)
    await service.unfollow(str(user.id), user_id)


@router.get(
    "/{user_id}/followers",
    summary="List followers",
    description="Returns a paginated list of user IDs who follow the given user.",
    response_description="Paginated list of follower user IDs",
)
async def list_followers(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, le=100, description="Number of results per page (max 100)"),
    session: AsyncSession = Depends(get_session),
):
    service = FollowService(session)
    items, total = await service.list_followers(user_id, page, size)
    return {
        "items": [item.follower_id for item in items],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get(
    "/{user_id}/following",
    summary="List following",
    description="Returns a paginated list of user IDs that the given user follows.",
    response_description="Paginated list of followed user IDs",
)
async def list_following(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, le=100, description="Number of results per page (max 100)"),
    session: AsyncSession = Depends(get_session),
):
    service = FollowService(session)
    items, total = await service.list_following(user_id, page, size)
    return {
        "items": [item.followed_id for item in items],
        "total": total,
        "page": page,
        "size": size,
    }
