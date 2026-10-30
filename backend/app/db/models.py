"""PostgreSQL models for analysis jobs, reports and execution events.

No secrets, prompts or repository file contents are stored here. JSONB columns hold data shaped
by the Pydantic models in ``app.schemas.evidence``.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import EventStatus, JobStatus
from app.core.limits import MAX_CODE_LENGTH, MAX_REPO_URL_LENGTH
from app.db.base import Base, str_enum

EMPTY_JSON_ARRAY = text("'[]'::jsonb")
EMPTY_JSON_OBJECT = text("'{}'::jsonb")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Normalized https://github.com/<owner>/<repo> form.
    repo_url: Mapped[str] = mapped_column(String(MAX_REPO_URL_LENGTH))
    question: Mapped[str] = mapped_column(Text)
    status: Mapped[JobStatus] = mapped_column(
        str_enum(JobStatus, "job_status"),
        default=JobStatus.QUEUED,
        server_default=JobStatus.QUEUED.value,
    )
    # An ErrorCode value; a plain string so later phases can add codes without a migration.
    error_code: Mapped[str | None] = mapped_column(String(MAX_CODE_LENGTH))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    report: Mapped["Report | None"] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    events: Mapped[list["ExecutionEvent"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="ExecutionEvent.sequence",
    )

    __table_args__ = (Index("ix_analysis_jobs_status_created_at", "status", "created_at"),)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"), unique=True
    )
    summary: Mapped[str] = mapped_column(Text)
    # Lists of Finding, Recommendation and SourceReference (app.schemas.evidence).
    findings: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, server_default=EMPTY_JSON_ARRAY
    )
    recommendations: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, server_default=EMPTY_JSON_ARRAY
    )
    sources: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, server_default=EMPTY_JSON_ARRAY
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped[AnalysisJob] = relationship(back_populates="report")


class ExecutionEvent(Base):
    __tablename__ = "execution_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_jobs.id", ondelete="CASCADE"))
    # Order of events within a job, starting at 1.
    sequence: Mapped[int]
    event_type: Mapped[str] = mapped_column(String(MAX_CODE_LENGTH))
    # An EventComponent value; a plain string so new components need no migration.
    component: Mapped[str] = mapped_column(String(MAX_CODE_LENGTH))
    status: Mapped[EventStatus] = mapped_column(str_enum(EventStatus, "event_status"))
    duration_ms: Mapped[int | None]
    # Small diagnostic fields only: never prompts, source content or secrets.
    details: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=EMPTY_JSON_OBJECT
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped[AnalysisJob] = relationship(back_populates="events")

    __table_args__ = (UniqueConstraint("job_id", "sequence"),)
