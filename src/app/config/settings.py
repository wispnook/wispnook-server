from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local")
    log_level: str = Field(default="INFO")
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/social_network"
    )
    jwt_secret: str = "dev-secret"
    jwt_exp_minutes: int = Field(default=30, ge=5)
    jwt_refresh_exp_minutes: int = Field(default=60 * 24 * 30, ge=60)
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_client_id: str = "social-network-api"
    kafka_security_protocol: str = "PLAINTEXT"
    kafka_group_id: str = "social-network-consumer"
    kafka_topics: str = "user.created,user.followed,post.created,post.liked,comment.created"
    redis_url: str = Field(default="redis://localhost:6379/0")
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    otel_exporter_otlp_endpoint: str | None = None
    otel_service_name: str = "social-network-api"
    prometheus_metrics_port: int = 9000
    admin_email: str = "admin@example.com"
    admin_password: str = "ChangeMe123!"
    idempotency_ttl_seconds: int = 86400
    outbox_dispatch_interval_seconds: int = 5

    @property
    def kafka_topic_list(self) -> list[str]:
        return [topic.strip() for topic in self.kafka_topics.split(",") if topic.strip()]


settings = Settings()
