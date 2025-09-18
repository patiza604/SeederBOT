import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .logging_config import LoggerAdapter, get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Extract client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Create logger with request context
        request_logger = LoggerAdapter(
            logger,
            {
                'request_id': request_id,
                'client_ip': client_ip,
                'user_agent': user_agent,
            }
        )

        # Log request start
        start_time = time.time()
        request_logger.info(
            "Request started",
            extra={
                'event': 'request_start',
                'method': request.method,
                'url': str(request.url),
                'path': request.url.path,
                'query_params': dict(request.query_params),
            }
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log successful response
            request_logger.info(
                "Request completed",
                extra={
                    'event': 'request_complete',
                    'status_code': response.status_code,
                    'process_time_ms': round(process_time * 1000, 2),
                }
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # Calculate processing time
            process_time = time.time() - start_time

            # Log error
            request_logger.error(
                "Request failed",
                extra={
                    'event': 'request_error',
                    'error_type': type(exc).__name__,
                    'error_message': str(exc),
                    'process_time_ms': round(process_time * 1000, 2),
                },
                exc_info=True
            )

            # Re-raise the exception
            raise
