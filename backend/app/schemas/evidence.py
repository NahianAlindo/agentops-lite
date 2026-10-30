"""Evidence models stored in report JSONB columns and returned by the API.

Every finding and recommendation must cite at least one source, so unsupported claims cannot be
represented.
"""

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import SourceKind
from app.core.limits import (
    MAX_EVIDENCE_EXCERPT_LENGTH,
    MAX_SOURCE_LOCATION_LENGTH,
    MAX_STATEMENT_LENGTH,
    MAX_TITLE_LENGTH,
)


class SourceReference(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: SourceKind
    # Repository file path, or documentation URL.
    location: str = Field(min_length=1, max_length=MAX_SOURCE_LOCATION_LENGTH)
    title: str | None = Field(default=None, max_length=MAX_TITLE_LENGTH)
    # A short supporting passage, never a whole file.
    excerpt: str | None = Field(default=None, max_length=MAX_EVIDENCE_EXCERPT_LENGTH)
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)


class Finding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    statement: str = Field(min_length=1, max_length=MAX_STATEMENT_LENGTH)
    evidence: list[SourceReference] = Field(min_length=1)


class Recommendation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    action: str = Field(min_length=1, max_length=MAX_STATEMENT_LENGTH)
    rationale: str = Field(min_length=1, max_length=MAX_STATEMENT_LENGTH)
    evidence: list[SourceReference] = Field(min_length=1)
