"""Middleware for exception handling and request/response logging."""

import logging
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
import httpx
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_error_response(
    request: Request,
    request_id: str,
    start_time: float,
    *,
    status_code: int,
    error: str,
    detail: str,
    error_type: str,
    log_message: str | None = None,
    log_level: int = logging.ERROR,
    exc_info: bool = False,
) -> JSONResponse:
    """Log an error with request context and build a consistent JSON error response."""
    process_time = time.time() - start_time
    logger.log(
        log_level,
        log_message or error,
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "error": detail,
            "error_type": error_type,
            "process_time_ms": round(process_time * 1000, 2),
        },
        exc_info=exc_info,
    )
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error,
            "detail": detail,
            "request_id": request_id,
        }
    )


class ExceptionHandlerMiddleware:
    """Global exception handler middleware for FastAPI applications.
    
    - Logs all unhandled exceptions with request context
    - Returns consistent error responses
    - Handles database and connection errors gracefully
    """
    
    async def __call__(
        self, request: Request, call_next: Callable
    ) -> Response | JSONResponse:
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Add request ID to request state for logging
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            
            # Log successful requests
            process_time = time.time() - start_time
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time * 1000, 2),
                    "user_agent": request.headers.get("user-agent", ""),
                    "client_ip": request.client.host if request.client else None,
                }
            )
            
            return response
            
        except SQLAlchemyError as e:
            # Database-related errors
            return _build_error_response(
                request, request_id, start_time,
                status_code=500,
                error="Internal server error",
                detail="A database error occurred",
                error_type="database",
                log_message="Database error occurred",
                exc_info=True,
            )

        except httpx.RequestError as e:
            # External service connection errors
            return _build_error_response(
                request, request_id, start_time,
                status_code=502,
                error="Bad gateway",
                detail="External service unavailable",
                error_type="external_service",
                log_message="External service error",
                exc_info=True,
            )

        except ValueError as e:
            # Input validation errors
            return _build_error_response(
                request, request_id, start_time,
                status_code=400,
                error="Bad request",
                detail=str(e),
                error_type="validation",
                log_message="Validation error",
                log_level=logging.WARNING,
            )

        except Exception as e:
            # Catch-all for any other unhandled exceptions
            # In production, don't expose internal error details
            detail = str(e) if settings.debug else "An internal error occurred"
            return _build_error_response(
                request, request_id, start_time,
                status_code=500,
                error="Internal server error",
                detail=detail,
                error_type="unhandled",
                log_message="Unhandled exception occurred",
                exc_info=True,
            )


async def log_request_response(
    request: Request,
    call_next: Callable,
) -> Response:
    """Middleware to log request/response details for debugging.
    
    This is a lightweight logging middleware that can be enabled/disabled
    via configuration for sensitive environments.
    """
    if not settings.log_requests:
        return await call_next(request)
    
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Log request details (excluding sensitive headers)
    safe_headers = {
        k: "***REDACTED***" if k.lower() in ("authorization", "x-api-key") else v
        for k, v in request.headers.items()
    }
    
    logger.debug(
        "Incoming request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "headers": safe_headers,
            "client_ip": request.client.host if request.client else None,
        }
    )
    
    # Process request
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log response details
    logger.debug(
        "Outgoing response",
        extra={
            "request_id": request_id,
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2),
            "response_headers": dict(response.headers),
        }
    )
    
    return response