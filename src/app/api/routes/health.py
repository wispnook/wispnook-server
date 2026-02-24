from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/liveness")
async def liveness():
    return {"status": "ok"}


@router.get("/readiness")
async def readiness():
    return {"status": "ready"}
