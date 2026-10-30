"""Application settings.

Plain settings come from environment variables (case-insensitive, for example ``DATABASE_HOST``).
Secrets come from files in the secrets directory; each file is named after its field (see
docs/secrets.md). Per-mode defaults and startup safety guards are added in Stage 4.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.enums import AppEnv

# backend/app/core/config.py -> repository root. The app runs from backend/, but the dev
# secrets directory lives at the repository root.
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SECRETS_DIR = REPO_ROOT / "secrets"

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        secrets_dir=DEFAULT_SECRETS_DIR,
        extra="ignore",
        frozen=True,
    )

    # --- Runtime mode ---
    app_env: AppEnv = AppEnv.DEV
    # None means "use the mode's default" (see Stage 0 section 3a).
    log_level: LogLevel | None = None
    docs_enabled: bool | None = None
    cors_origins: list[str] = Field(default_factory=list)
    # Trust X-Forwarded-For for the client address only behind a known proxy.
    trusted_proxy: bool = False

    # --- PostgreSQL ---
    database_host: str = "localhost"
    database_port: int = Field(default=5432, ge=1, le=65535)
    database_name: str = "agentops"
    database_user: str = "agentops"
    database_password: SecretStr
    database_pool_size: int = Field(default=5, ge=1)
    database_max_overflow: int = Field(default=5, ge=0)
    database_connect_timeout_s: float = Field(default=5.0, gt=0)
    database_statement_timeout_ms: int = Field(default=10_000, gt=0)
    migration_retry_window_s: float = Field(default=30.0, gt=0)

    # --- Qdrant ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: SecretStr | None = None
    qdrant_collection: str = "documentation_chunks"
    qdrant_vector_size: int = Field(default=384, gt=0)
    qdrant_distance: Literal["cosine", "dot", "euclid"] = "cosine"

    # --- Redis (rate-limit counters only) ---
    redis_url: str = "redis://localhost:6379/0"
    redis_password: SecretStr | None = None

    # --- Request limits ---
    rate_limit_enabled: bool = True
    rate_limit_job_create_per_minute: int = Field(default=5, gt=0)
    rate_limit_read_per_minute: int = Field(default=60, gt=0)
    max_request_body_bytes: int = Field(default=64 * 1024, gt=0)
    request_timeout_s: float = Field(default=30.0, gt=0)

    # --- Telemetry (exporters are wired in Phase 1b) ---
    otel_enabled: bool = False
    otel_service_name: str = "agentops-lite"
    otel_exporter_otlp_endpoint: str | None = None
