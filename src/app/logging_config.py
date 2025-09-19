import logging
import sys
from datetime import datetime, timezone
from typing import Any

# Compatibility for different Python versions and packages
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

try:
    from pythonjsonlogger.json import JsonFormatter
except ImportError:
    from pythonjsonlogger import jsonlogger
    JsonFormatter = jsonlogger.JsonFormatter


class StructuredFormatter(JsonFormatter):
    """Custom JSON formatter with structured fields."""

    def add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        log_record['timestamp'] = datetime.now(UTC).isoformat()

        # Add service info
        log_record['service'] = 'seederbot'
        log_record['version'] = '0.1.0'

        # Add log level
        log_record['level'] = record.levelname

        # Add module and function context
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno

        # Add request context if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_agent'):
            log_record['user_agent'] = record.user_agent
        if hasattr(record, 'client_ip'):
            log_record['client_ip'] = record.client_ip


def setup_logging(level: str = "INFO", structured: bool = True) -> None:
    """Setup application logging configuration."""

    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    if structured:
        # Use structured JSON logging
        formatter = StructuredFormatter(
            '%(timestamp)s %(level)s %(service)s %(version)s %(module)s %(function)s %(message)s'
        )
    else:
        # Use simple text logging for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for adding request context."""

    def __init__(self, logger: logging.Logger, extra: dict[str, Any] = None):
        super().__init__(logger, extra or {})

    def process(self, msg: Any, kwargs: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        # Add extra context to log record
        kwargs['extra'] = {**self.extra, **kwargs.get('extra', {})}
        return msg, kwargs
