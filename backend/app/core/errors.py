"""Application error types.

Each ``AppError`` maps to one HTTP status and error code in the standard error envelope.
The exception handlers that produce the envelope are added in Stage 4.
"""

from typing import ClassVar

from app.core.enums import ErrorCode


class AppError(Exception):
    """Base class for errors that are reported to the client."""

    status_code: ClassVar[int] = 500
    code: ClassVar[ErrorCode] = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidInputError(AppError):
    status_code = 422
    code = ErrorCode.VALIDATION_ERROR


class NotFoundError(AppError):
    status_code = 404
    code = ErrorCode.NOT_FOUND


class PayloadTooLargeError(AppError):
    status_code = 413
    code = ErrorCode.PAYLOAD_TOO_LARGE


class RateLimitedError(AppError):
    status_code = 429
    code = ErrorCode.RATE_LIMITED

    def __init__(self, message: str, retry_after_seconds: int) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class RequestTimeoutError(AppError):
    status_code = 504
    code = ErrorCode.REQUEST_TIMEOUT


class DependencyUnavailableError(AppError):
    """A required dependency is down. ``dependency`` is a name only, never connection details."""

    status_code = 503
    code = ErrorCode.DEPENDENCY_UNAVAILABLE

    def __init__(self, message: str, dependency: str) -> None:
        super().__init__(message)
        self.dependency = dependency


class StartupError(Exception):
    """The app cannot start: missing secret, failed migration, or an unsafe configuration.

    Not an ``AppError``: it is never sent to a client. Messages name the problem (for example
    the missing secret's file name) and never include secret values.
    """
