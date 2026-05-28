"""
Custom exception classes for OrgFlow Agent
"""

from typing import Any, Optional

from app.exceptions.error_codes import ErrorCode


class OrgFlowException(Exception):
    """Base exception for all OrgFlow errors"""

    def __init__(
        self,
        message: str,
        error_code: str = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(OrgFlowException):
    """Raised when input validation fails"""

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details=details,
        )


class NotFoundError(OrgFlowException):
    """Raised when a resource is not found"""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            details=details,
        )


class UnauthorizedError(OrgFlowException):
    """Raised when authentication fails"""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=401,
        )


class ForbiddenError(OrgFlowException):
    """Raised when user lacks permission"""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            error_code=ErrorCode.FORBIDDEN,
            status_code=403,
        )


class ConflictError(OrgFlowException):
    """Raised when resource conflict occurs (e.g., duplicate)"""

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFLICT,
            status_code=409,
            details=details,
        )


class RateLimitError(OrgFlowException):
    """Raised when rate limit is exceeded"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=details,
        )


class ServiceUnavailableError(OrgFlowException):
    """Raised when external service is unavailable"""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        error_details = details or {}
        if service_name:
            error_details["service_name"] = service_name

        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=503,
            details=error_details,
        )


class ExternalAPIError(OrgFlowException):
    """Raised when external API call fails"""

    def __init__(
        self,
        message: str,
        api_name: Optional[str] = None,
        status_code_from_api: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        error_details = details or {}
        if api_name:
            error_details["api_name"] = api_name
        if status_code_from_api:
            error_details["external_status_code"] = status_code_from_api

        super().__init__(
            message=message,
            error_code=ErrorCode.EXTERNAL_API_ERROR,
            status_code=502,
            details=error_details,
        )


class DatabaseError(OrgFlowException):
    """Raised when database operation fails"""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        error_details = details or {}
        if operation:
            error_details["operation"] = operation

        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=500,
            details=error_details,
        )


class ConfigurationError(OrgFlowException):
    """Raised when configuration is invalid"""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        error_details = details or {}
        if config_key:
            error_details["config_key"] = config_key

        super().__init__(
            message=message,
            error_code=ErrorCode.CONFIGURATION_ERROR,
            status_code=500,
            details=error_details,
        )
