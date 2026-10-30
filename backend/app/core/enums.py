"""Enumerations shared by the database models, API schemas and services."""

from enum import StrEnum


class AppEnv(StrEnum):
    """Runtime mode, selected by the APP_ENV setting."""

    DEV = "dev"
    TEST = "test"
    PRODUCTION = "production"


class JobStatus(StrEnum):
    """Lifecycle of an analysis job: queued -> running -> completed | failed | timed_out."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class EventComponent(StrEnum):
    """The part of the system that produced an execution event."""

    API = "api"
    ORCHESTRATOR = "orchestrator"
    REPOSITORY_ANALYST = "repository_analyst"
    DOCUMENTATION_RESEARCHER = "documentation_researcher"
    ENGINEERING_REVIEWER = "engineering_reviewer"
    MCP = "mcp"
    RAG = "rag"
    LLM = "llm"


class EventStatus(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class DependencyState(StrEnum):
    """Readiness state of one external dependency (PostgreSQL, Qdrant, Redis)."""

    OK = "ok"
    DEGRADED = "degraded"
    FAILED = "failed"


class SourceKind(StrEnum):
    """Where a piece of report evidence came from."""

    REPOSITORY_FILE = "repository_file"
    DOCUMENTATION = "documentation"


class ErrorCode(StrEnum):
    """Machine-readable error codes returned in the error envelope.

    Later phases add job failure reasons (for example LLM provider errors); the
    ``analysis_jobs.error_code`` column is a plain string so that adding a code needs no
    migration.
    """

    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    RATE_LIMITED = "rate_limited"
    PAYLOAD_TOO_LARGE = "payload_too_large"
    REQUEST_TIMEOUT = "request_timeout"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    INTERNAL_ERROR = "internal_error"
