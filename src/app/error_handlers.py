"""Global error handlers for the FastAPI application."""

import traceback

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from .exceptions import SeederBotException
from .logging_config import LoggerAdapter, get_logger

logger = get_logger(__name__)


async def seederbot_exception_handler(request: Request, exc: SeederBotException) -> JSONResponse:
    """Handle custom SeederBot exceptions."""

    # Create logger with request context
    request_logger = LoggerAdapter(
        logger,
        {
            'request_id': getattr(request.state, 'request_id', 'unknown'),
            'client_ip': request.client.host if request.client else 'unknown',
        }
    )

    request_logger.error(
        "SeederBot exception occurred",
        extra={
            'event': 'seederbot_exception',
            'exception_type': type(exc).__name__,
            'status_code': exc.status_code,
            'exception_details': exc.details,
            'path': request.url.path,
            'method': request.method,
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.message,
            "details": exc.details,
            "type": type(exc).__name__
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions."""

    request_logger = LoggerAdapter(
        logger,
        {
            'request_id': getattr(request.state, 'request_id', 'unknown'),
            'client_ip': request.client.host if request.client else 'unknown',
        }
    )

    # Log based on severity
    if exc.status_code >= 500:
        request_logger.error(
            "HTTP server error",
            extra={
                'event': 'http_server_error',
                'status_code': exc.status_code,
                'path': request.url.path,
                'method': request.method,
            }
        )
    elif exc.status_code >= 400:
        request_logger.warning(
            "HTTP client error",
            extra={
                'event': 'http_client_error',
                'status_code': exc.status_code,
                'path': request.url.path,
                'method': request.method,
            }
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "type": "HTTPException"
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""

    request_logger = LoggerAdapter(
        logger,
        {
            'request_id': getattr(request.state, 'request_id', 'unknown'),
            'client_ip': request.client.host if request.client else 'unknown',
        }
    )

    # Extract validation error details
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    request_logger.warning(
        "Request validation failed",
        extra={
            'event': 'validation_error',
            'validation_errors': validation_errors,
            'path': request.url.path,
            'method': request.method,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Request validation failed",
            "details": {
                "validation_errors": validation_errors
            },
            "type": "ValidationError"
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""

    request_logger = LoggerAdapter(
        logger,
        {
            'request_id': getattr(request.state, 'request_id', 'unknown'),
            'client_ip': request.client.host if request.client else 'unknown',
        }
    )

    # Log the full exception with stack trace
    request_logger.error(
        "Unexpected exception occurred",
        extra={
            'event': 'unexpected_exception',
            'exception_type': type(exc).__name__,
            'path': request.url.path,
            'method': request.method,
            'traceback': traceback.format_exc(),
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An unexpected error occurred",
            "type": "InternalServerError",
            "request_id": getattr(request.state, 'request_id', 'unknown')
        }
    )
