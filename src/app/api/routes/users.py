from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.common import get_current_user, get_session
from app.domain.schemas.users import UserOut, UserPublic, UserSearchResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user=Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):
    service = UserService(session)
    updated = await service.update_profile(str(user.id), payload)
    return UserOut.model_validate(updated)


@router.get("", response_model=UserSearchResponse)
async def search_users(
    query: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    items, total = await service.search(query, page, size)
    return UserSearchResponse(
        items=[UserPublic(id=item.id, username=item.username, bio=item.bio) for item in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: str, session: AsyncSession = Depends(get_session)):
    service = UserService(session)
    user = await service.me(user_id)
    return UserPublic.model_validate(user)
