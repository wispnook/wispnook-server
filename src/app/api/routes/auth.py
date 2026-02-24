from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.common import get_session
from app.domain.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.rate_limit.dependency import rate_limiter
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenPair,
    status_code=201,
    dependencies=[Depends(rate_limiter)],
    summary="Register a new user",
    description="Create a new account with a unique email and username. Returns a JWT access/refresh token pair on success.",
    response_description="JWT token pair for the newly created user",
)
async def register(payload: RegisterRequest, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    return await service.register_user(
        email=payload.email,
        username=payload.username,
        password=payload.password,
        bio=payload.bio,
    )


@router.post(
    "/login",
    response_model=TokenPair,
    dependencies=[Depends(rate_limiter)],
    summary="Login",
    description="Authenticate with username and password. Returns a JWT access/refresh token pair.",
    response_description="JWT token pair for the authenticated user",
)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    return await service.login(username=payload.username, password=payload.password)


@router.post(
    "/refresh",
    response_model=TokenPair,
    dependencies=[Depends(rate_limiter)],
    summary="Refresh tokens",
    description="Exchange a valid refresh token for a new access/refresh token pair. The old refresh token is invalidated.",
    response_description="New JWT token pair",
)
async def refresh(payload: RefreshRequest, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    return await service.rotate_refresh_token(payload.refresh_token)
