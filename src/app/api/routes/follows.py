from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.common import get_current_user, get_session
from app.rate_limit.dependency import rate_limiter
from app.services.follow_service import FollowService

router = APIRouter(prefix="/follows", tags=["follows"])


@router.post("/{user_id}", status_code=204, dependencies=[Depends(rate_limiter)])
async def follow_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    service = FollowService(session)
    await service.follow(str(user.id), user_id)


@router.delete("/{user_id}", status_code=204, dependencies=[Depends(rate_limiter)])
async def unfollow_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    service = FollowService(session)
    await service.unfollow(str(user.id), user_id)


@router.get("/{user_id}/followers")
async def list_followers(
    user_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
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


@router.get("/{user_id}/following")
async def list_following(
    user_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
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
