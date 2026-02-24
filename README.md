🔥 Wispnook

Wisp → quiet, fleeting, private conversations
Nook → safe, intentional, human-scale spaces

A production-ready social network backend built with FastAPI, PostgreSQL, Redis, and Kafka. It demonstrates clean
architecture, event-driven design, and strong operational tooling (observability, testing, CI/CD, containers).

## Architecture Overview

The service follows a layered design:

- **API layer** (`app/api`): FastAPI routers + dependency injection, request validation via Pydantic v2.
- **Services** (`app/services`): Business logic for users, posts, follows, feed, auth.
- **Repositories** (`app/repositories`): Isolated SQLAlchemy ORM data access.
- **Events** (`app/events`): Outbox pattern + aiokafka producers/consumers to publish and consume domain events.
- **Caching & Rate limiting** (`app/cache`, `app/rate_limit`): Redis-powered caching and per-IP rate limiting.
- **Observability** (`app/observability`): Structured logging with structlog, Prometheus metrics, optional OpenTelemetry
  tracing.

### Components

- **FastAPI**: Async endpoints, OAuth2 password flow, OpenAPI docs.
- **SQLAlchemy 2.0 + Alembic**: Async ORM, migrations in `alembic/`.
- **PostgreSQL**: Primary data store.
- **Redis**: Feed cache, like counts, idempotency keys, rate limiting, event idempotency.
- **Kafka (aiokafka)**: JSON events for users, posts, likes, comments. Outbox dispatcher publishes after DB commit.
- **Docker Compose**: Local stack with API, Postgres, Redis, Kafka, Zookeeper.
- **Testing**: `pytest` unit/integration/contract suites, coverage >= 85% (configured).
- **Tooling**: Makefile targets, GitHub Actions CI to lint, type check, test, and build image.

> **Kafka choice**: `aiokafka` keeps the stack async-friendly and integrates smoothly with FastAPI's event loop,
> enabling consistent async producer/consumer lifecycles.

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11 (for local dev outside containers)

### Environment

Copy `.env.example` to `.env` and tweak values (DB URL, JWT secret, Kafka servers, etc.).

```
cp .env.example .env
```

### Makefile Commands

- `make setup` – create virtualenv and install dependencies.
- `make lint` / `make format` – code quality tooling (black, isort, flake8).
- `make typecheck` – run mypy.
- `make test` – unit tests.
- `make test-integration` – integration tests (marked with `@pytest.mark.integration`).
- `make coverage` – full pytest suite with coverage (HTML + XML outputs).
- `make up` / `make down` – start/stop Docker Compose stack.
- `make migrate` – run Alembic migrations.
- `make revision` – autogenerate a new migration.

### Running Locally

1. **Install deps (optional)**
   ```bash
   make setup
   source .venv/bin/activate
   ```
2. **Start infrastructure**
   ```bash
   docker-compose up --build
   ```
3. API available at `http://localhost:8000`.

### API Documentation

FastAPI serves interactive documentation automatically:

| URL                                  | Interface                                          |
|--------------------------------------|----------------------------------------------------|
| `http://localhost:8000/docs`         | Swagger UI — try endpoints directly in the browser |
| `http://localhost:8000/redoc`        | ReDoc — clean, readable reference                  |
| `http://localhost:8000/openapi.json` | Raw OpenAPI 3.1 schema                             |

To authenticate in Swagger UI, click **Authorize** and enter `Bearer <access_token>` obtained from `POST /auth/login`.

### Database Migrations

Apply migrations (local Python environment must see DB):

```bash
make migrate
```

to create new migrations:

```bash
make revision
```

### Kafka Topics & Events

Topics created automatically via `docker/create-topics.sh`:

- `user.created`
- `user.followed`
- `post.created`
- `post.liked`
- `comment.created`

Event payloads are all JSON and validated by Pydantic models in `app/domain/events/schemas.py`. Contract tests cover
serialization.

### Observability

- Structured JSON logs with request IDs.
- Prometheus metrics exposed via Instrumentator at `/metrics`.
- Optional OTLP tracing (set `OTEL_EXPORTER_OTLP_ENDPOINT`).
- Graceful degradation when observability endpoints are unavailable.

### Rate Limiting & Caching

- Redis-based token bucket for write endpoints.
- Feed responses cached per user for 60 seconds.
- Like counts cached in Redis hashes.
- Idempotency keys (Redis) for post creation.
- Kafka consumers track processed IDs in Redis to avoid duplicates.

### Testing

```
make test          # unit tests
make test-integration
make coverage
```

Integration tests spin up an in-memory SQLite DB + stubbed Redis/Kafka to validate FastAPI routes. Contract tests ensure
Kafka payloads remain backwards-compatible.

### CI/CD

GitHub Actions workflow `.github/workflows/ci.yml`:

1. Install deps
2. Lint
3. Type check
4. Run tests & upload coverage
5. Build Docker image on `main`

### Troubleshooting

- **Kafka not ready**: ensure `kafka-init` container finishes creating topics.
- **Migrations fail**: confirm `DATABASE_URL` matches `docker-compose` service.
- **Redis connection errors**: check `REDIS_URL` env and Compose ports.
- **Tests hitting real services**: ensure `.env` sets `APP_ENV=test` or run via `make test` (fixtures stub external
  systems).
- **Passlib deprecation warning**: This is a known issue with passlib 1.7.4 and Python 3.11+. The warning can be safely
  ignored until passlib releases an update.

### Extending

- Add admin-only moderation endpoints in `app/api/routes/posts.py`.
- Implement refresh token rotation in `AuthService.rotate_refresh_token`.
- Add background task to rebuild feed caches periodically.
- Integrate object storage for media uploads (presigned URL stub in `PostService`).

### API Surface

| Method | Path                      | Description                               |
|--------|---------------------------|-------------------------------------------|
| POST   | `/auth/register`          | Register and auto-login user              |
| POST   | `/auth/login`             | Username/password login                   |
| POST   | `/auth/refresh`           | Rotate refresh token                      |
| GET    | `/users/me`               | Authenticated profile                     |
| PATCH  | `/users/me`               | Update profile                            |
| GET    | `/users`                  | Search users                              |
| GET    | `/users/{id}`             | Public profile                            |
| POST   | `/follows/{id}`           | Follow user                               |
| DELETE | `/follows/{id}`           | Unfollow user                             |
| GET    | `/users/{id}/followers`   | List followers                            |
| GET    | `/users/{id}/following`   | List following                            |
| POST   | `/posts`                  | Create post (text + optional media)       |
| GET    | `/posts`                  | List posts (pagination, filter by author) |
| GET    | `/posts/{id}`             | Post detail                               |
| DELETE | `/posts/{id}`             | Delete post (author/admin)                |
| POST   | `/posts/{id}/likes`       | Like post                                 |
| DELETE | `/posts/{id}/likes`       | Unlike post                               |
| GET    | `/posts/{id}/likes/count` | Like counter                              |
| POST   | `/posts/{id}/comments`    | Comment on post                           |
| GET    | `/posts/{id}/comments`    | List comments                             |
| DELETE | `/comments/{id}`          | Delete comment                            |
| GET    | `/feed`                   | Timeline from followed users              |
| GET    | `/health/liveness`        | Liveness probe                            |
| GET    | `/health/readiness`       | Readiness probe                           |

## License

MIT
