"""Middleware for exception handling and request/response logging."""

import logging
import time
import uuid
from datetime import datetime
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
import httpx
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware:
    """Global exception handler middleware for FastAPI applications.
    
    - Logs all unhandled exceptions with request context
    - Returns consistent error responses
    - Handles database and connection errors gracefully
    """
    
    async def __call__(
        self, request: Request, call_next
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
                f"Request completed",
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
            process_time = time.time() - start_time
            
            logger.error(
                "Database error occurred",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "error_type": "database",
                    "process_time_ms": round(process_time * 1000, 2),
                },
                exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "detail": "A database error occurred",
                    "request_id": request_id,
                }
            )
            
        except httpx.RequestError as e:
            # External service connection errors
            process_time = time.time() - start_time
            
            logger.error(
                "External service error",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "error_type": "external_service",
                    "process_time_ms": round(process_time * 1000, 2),
                },
                exc_info=True
            )
            
            return JSONResponse(
                status_code=502,
                content={
                    "error": "Bad gateway",
                    "detail": "External service unavailable",
                    "request_id": request_id,
                }
            )
            
        except ValueError as e:
            # Input validation errors
            process_time = time.time() - start_time
            
            logger.warning(
                "Validation error",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "error_type": "validation",
                    "process_time_ms": round(process_time * 1000, 2),
                }
            )
            
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Bad request",
                    "detail": str(e),
                    "request_id": request_id,
                }
            )
            
        except Exception as e:
            # Catch-all for any other unhandled exceptions
            process_time = time.time() - start_time
            
            logger.exception(
                "Unhandled exception occurred",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "error_type": "unhandled",
                    "process_time_ms": round(process_time * 1000, 2),
                }
            )
            
            # In production, don't expose internal error details
            if settings.debug:
                detail = str(e)
            else:
                detail = "An internal error occurred"
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "detail": detail,
                    "request_id": request_id,
                }
            )


async def log_request_response(
    request: Request,
    call_next
) -> Response:
    """Middleware to log request/response details for debugging.
    
    This is a lightweight logging middleware that can be enabled/disabled
    via configuration for sensitive environments.
    """
    if not getattr(settings, "log_requests", False):
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