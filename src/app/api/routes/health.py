from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "/liveness",
    summary="Liveness probe",
    description="Returns 200 when the application process is running. Used by container orchestrators to detect crashes.",
    response_description="Static OK status",
)
async def liveness():
    return {"status": "ok"}


@router.get(
    "/readiness",
    summary="Readiness probe",
    description="Returns 200 when the application is ready to serve traffic. Used by container orchestrators to gate request routing.",
    response_description="Static ready status",
)
async def readiness():
    return {"status": "ready"}
