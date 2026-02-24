# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
make setup              # Create virtualenv & install deps
make install            # Install deps to current Python

# Development
make format             # Auto-format with black + isort
make lint               # Check formatting and flake8
make typecheck          # Run mypy

# Testing
make test               # Run unit tests only
make test-integration   # Run integration tests (require Docker services)
make coverage           # Full test suite with coverage report (target: 85%)

# Run a single test file
pytest tests/unit/test_post_service.py -v

# Run a single test by name
pytest tests/unit/test_post_service.py::test_create_post -v

# Docker stack
make up                 # Start PostgreSQL, Redis, Kafka, API
make down               # Stop and clean up
make logs               # Tail API container logs

# Migrations
make migrate            # Run Alembic migrations
make revision           # Auto-generate new migration from model changes
```

Copy `.env.example` to `.env` before starting the local stack.

## Architecture

**Layered architecture:** `API routes → Services → Repositories → Domain`

### Layers

- **`src/app/api/routes/`** — FastAPI routers (auth, users, posts, comments, follows, feed, health). Rate limiting applied to write operations. All endpoints use `Depends()` for session, Redis, and auth.
- **`src/app/services/`** — Business logic. Services use repositories for data access and publish domain events via the outbox pattern.
- **`src/app/repositories/`** — SQLAlchemy async queries. `BaseRepository` provides `get_by_id`. Specialized repos for each aggregate.
- **`src/app/domain/`** — Three sub-packages:
  - `models/` — SQLAlchemy ORM models using `UUIDMixin` and `TimestampMixin` from `base.py`
  - `schemas/` — Pydantic v2 request/response schemas
  - `events/` — Kafka event schemas and `EVENT_TOPIC_MAP` for deserialization

### Cross-Cutting Infrastructure

- **`src/app/events/`** — Outbox dispatcher polls `event_outbox` table, publishes to Kafka. Consumer handles idempotency via Redis keys. Five topics: `user.created`, `user.followed`, `post.created`, `post.liked`, `comment.created`.
- **`src/app/cache/redis_client.py`** — Redis wrapper; used for feed caching (60s TTL), like counts (Redis hashes), idempotency keys, and token-bucket rate limiting.
- **`src/app/auth/security.py`** — JWT encode/decode and bcrypt password hashing.
- **`src/app/config/settings.py`** — Pydantic `BaseSettings` loaded from `.env`. Access via `get_settings()`.
- **`src/app/observability/`** — structlog JSON logging with request IDs, Prometheus metrics, OTLP tracing.
- **`src/app/utils/`** — `DomainError` base exception; mapped to HTTP status codes by the global exception handler in `main.py`.

### App Lifecycle (`src/app/main.py`)

Startup: Redis init → Kafka producer start → Kafka consumer start → Outbox dispatcher start.
Shutdown: Graceful stop in reverse order. `RequestIdMiddleware` propagates `X-Request-ID` across the request/response cycle.

### Testing

- `tests/unit/` — Mocked dependencies, fast.
- `tests/integration/` — Marked `@pytest.mark.integration`; use testcontainers (PostgreSQL, Redis, Kafka).
- `tests/contracts/` — Pydantic event schema backward-compatibility tests.
- Shared fixtures in `tests/conftest.py`.

### Code Style

- Line length: 100 characters (black, flake8, isort)
- isort profile: black
- mypy configured for strict async checking
- All DB/Redis/Kafka operations are async

## Commits

Never add `Co-Authored-By` lines to commit messages.

All commit messages must use the conventional commit format — this drives automatic semver:

| Prefix | When to use | Version bump |
|---|---|---|
| `feat:` | New feature or endpoint | minor |
| `fix:` | Bug fix | patch |
| `perf:` | Performance improvement | patch |
| `refactor:` | Code restructure, no behaviour change | none |
| `docs:` | Documentation only | none |
| `chore:` | Maintenance, deps, config | none |
| `style:` | Formatting, whitespace | none |
| `test:` | Adding or fixing tests | none |
| `build:` | Build system or Docker changes | none |
| `ci:` | CI/CD workflow changes | none |

For breaking changes, append `!` to the prefix (e.g. `feat!:`) or add a `BREAKING CHANGE:` footer → major bump.
