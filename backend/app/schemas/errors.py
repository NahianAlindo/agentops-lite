"""The single error envelope returned for every failed request: ``{"error": {...}}``."""

from pydantic import BaseModel, ConfigDict

from app.core.enums import ErrorCode


class FieldError(BaseModel):
    """One invalid input field, returned with ``validation_error``."""

    model_config = ConfigDict(frozen=True)

    field: str
    message: str


class ErrorBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: ErrorCode
    # Safe for clients: no stack traces, connection details or secret values.
    message: str
    request_id: str | None = None
    fields: list[FieldError] | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    error: ErrorBody
