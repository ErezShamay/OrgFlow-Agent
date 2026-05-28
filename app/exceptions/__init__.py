"""
Exception handling module for OrgFlow Agent
"""

from app.exceptions.exceptions import (
    OrgFlowException,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
    RateLimitError,
    ServiceUnavailableError,
    ExternalAPIError,
    DatabaseError,
    ConfigurationError,
)

from app.exceptions.middleware import (
    GlobalExceptionHandler,
    RequestLoggingMiddleware,
    ErrorResponse,
)
from app.exceptions.idempotency_middleware import (
    IdempotencyMiddleware,
)

from app.exceptions.logger import (
    setup_logging,
    get_logger,
    JSONFormatter,
)

__all__ = [
    "OrgFlowException",
    "ValidationError",
    "NotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
    "ConflictError",
    "RateLimitError",
    "ServiceUnavailableError",
    "ExternalAPIError",
    "DatabaseError",
    "ConfigurationError",
    "GlobalExceptionHandler",
    "RequestLoggingMiddleware",
    "IdempotencyMiddleware",
    "ErrorResponse",
    "setup_logging",
    "get_logger",
    "JSONFormatter",
]
