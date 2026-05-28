"""
Global exception handler middleware for OrgFlow Agent
"""

import traceback
import logging
import uuid
from datetime import datetime
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.exceptions.error_codes import ErrorCode
from app.exceptions.exceptions import OrgFlowException


# Configure logger
logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response format"""

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int,
        request_id: str,
        timestamp: str,
        path: str,
        method: str,
        details: dict = None,
        trace_id: str = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        self.timestamp = timestamp
        self.path = path
        self.method = method
        self.details = details or {}
        self.trace_id = trace_id

    def to_dict(self):
        response = {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.message,
                "status_code": self.status_code,
            },
            "metadata": {
                "request_id": self.request_id,
                "timestamp": self.timestamp,
                "path": self.path,
                "method": self.method,
            },
        }

        if self.details:
            response["error"]["details"] = self.details

        if self.trace_id:
            response["metadata"]["trace_id"] = self.trace_id

        return response


class GlobalExceptionHandler(BaseHTTPMiddleware):
    """
    Middleware to catch and handle all exceptions globally
    Provides structured error responses and logging
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None) or request.headers.get(
            "x-request-id",
            str(uuid.uuid4()),
        )
        trace_id = getattr(request.state, "trace_id", None) or request.headers.get(
            "x-trace-id",
            str(uuid.uuid4()),
        )

        # Attach request_id and trace_id to request state for downstream handlers
        request.state.request_id = request_id
        request.state.trace_id = trace_id

        try:
            response = await call_next(request)
            return response

        except OrgFlowException as exc:
            return self._handle_orgflow_exception(
                exc,
                request,
                request_id,
                trace_id,
            )

        except ValueError as exc:
            return self._handle_value_error(
                exc,
                request,
                request_id,
                trace_id,
            )

        except Exception as exc:
            return self._handle_generic_exception(
                exc,
                request,
                request_id,
                trace_id,
            )

    @staticmethod
    def _handle_orgflow_exception(
        exc: OrgFlowException,
        request: Request,
        request_id: str,
        trace_id: str,
    ) -> JSONResponse:
        """Handle OrgFlow-specific exceptions"""

        logger.warning(
            f"OrgFlow exception: {exc.error_code}",
            extra={
                "error_code": exc.error_code,
                "message": exc.message,
                "status_code": exc.status_code,
                "request_id": request_id,
                "trace_id": trace_id,
                "path": request.url.path,
                "method": request.method,
            },
        )

        error_response = ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            path=request.url.path,
            method=request.method,
            details=exc.details,
            trace_id=trace_id,
        )

        response = JSONResponse(
            status_code=exc.status_code,
            content=error_response.to_dict(),
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        return response

    @staticmethod
    def _handle_value_error(
        exc: ValueError,
        request: Request,
        request_id: str,
        trace_id: str,
    ) -> JSONResponse:
        """Handle value errors (invalid input)"""

        logger.warning(
            f"Validation error: {str(exc)}",
            extra={
                "error_code": ErrorCode.VALIDATION_ERROR,
                "request_id": request_id,
                "trace_id": trace_id,
                "path": request.url.path,
                "method": request.method,
            },
        )

        error_response = ErrorResponse(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            path=request.url.path,
            method=request.method,
            trace_id=trace_id,
        )

        response = JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.to_dict(),
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        return response

    @staticmethod
    def _handle_generic_exception(
        exc: Exception,
        request: Request,
        request_id: str,
        trace_id: str,
    ) -> JSONResponse:
        """Handle generic/unexpected exceptions"""

        # Log full traceback for debugging
        logger.error(
            f"Unexpected error: {type(exc).__name__}",
            extra={
                "error_code": ErrorCode.INTERNAL_ERROR,
                "request_id": request_id,
                "trace_id": trace_id,
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(),
            },
        )

        error_response = ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred. Please contact support if the problem persists.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            path=request.url.path,
            method=request.method,
            trace_id=trace_id,
        )

        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.to_dict(),
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to add request tracing metadata and structured request logs."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None) or request.headers.get(
            "x-request-id",
            str(uuid.uuid4()),
        )
        trace_id = getattr(request.state, "trace_id", None) or request.headers.get(
            "x-trace-id",
            str(uuid.uuid4()),
        )

        request.state.request_id = request_id
        request.state.trace_id = trace_id

        logger.info(
            "Request received",
            extra={
                "request_id": request_id,
                "trace_id": trace_id,
                "path": request.url.path,
                "method": request.method,
                "client": request.client.host if request.client else None,
            },
        )

        start_time = datetime.utcnow()

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "path": request.url.path,
                    "method": request.method,
                    "duration_ms": elapsed_ms,
                },
            )
            raise

        elapsed_ms = int(
            (datetime.utcnow() - start_time).total_seconds() * 1000
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id

        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "trace_id": trace_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": elapsed_ms,
            },
        )

        return response
