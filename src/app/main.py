from __future__ import annotations

import contextvars
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import auth, comments, feed, follows, health, posts, users
from app.cache.redis_client import redis_client
from app.db.session import SessionLocal
from app.events.consumer import consumer
from app.events.dispatcher import create_dispatcher
from app.events.producer import producer
from app.observability.logging import configure_logging, get_logger
from app.observability.metrics import setup_metrics
from app.observability.tracing import configure_tracing, instrument_app
from app.utils.exceptions import DomainError, to_http_exception

configure_logging()
configure_tracing()

logger = get_logger(__name__)
request_id_ctx_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

dispatcher = create_dispatcher(SessionLocal)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx_var.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan (startup and shutdown)."""
    # Startup
    redis_client.init()
    await producer.start()
    await consumer.start()
    await dispatcher.start()
    logger.info("Application started")

    yield

    # Shutdown
    await dispatcher.stop()
    await consumer.stop()
    await producer.stop()
    await redis_client.close()
    logger.info("Application stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Social Network API",
        version="0.1.0",
        description=(
            "Production-ready social network backend built with FastAPI, "
            "PostgreSQL, Redis, and Kafka.\n\n"
            "## Authentication\n\n"
            "Most endpoints require a Bearer JWT token. Obtain one via `POST /auth/login` or "
            "`POST /auth/register`, then pass it as:\n\n"
            "```\nAuthorization: Bearer <access_token>\n```\n\n"
            "## Rate Limiting\n\n"
            "Write endpoints are rate-limited per IP (default: 60 requests/minute). "
            "Exceeding the limit returns `429 Too Many Requests`.\n\n"
            "## Pagination\n\n"
            "All list endpoints accept `page` (1-indexed) and `size` (max 100) query parameters."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(follows.router)
    app.include_router(posts.router)
    app.include_router(comments.router)
    app.include_router(feed.router)
    app.include_router(health.router)

    setup_metrics(app)
    instrument_app(app)

    @app.exception_handler(DomainError)
    async def domain_exception_handler(_: Request, exc: DomainError) -> JSONResponse:
        http_exc = to_http_exception(exc)
        return JSONResponse(status_code=http_exc.status_code, content=http_exc.detail)

    return app


app = create_app()
