"""Custom exceptions for the SeederBot application."""

from typing import Any


class SeederBotException(Exception):
    """Base exception for SeederBot application."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        status_code: int = 500
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.status_code = status_code


class ConfigurationError(SeederBotException):
    """Raised when there's a configuration issue."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, details, status_code=500)


class ExternalServiceError(SeederBotException):
    """Raised when an external service (Radarr/Jackett) fails."""

    def __init__(self, service: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(f"{service} error: {message}", details, status_code=503)
        self.service = service


class ValidationError(SeederBotException):
    """Raised when request validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, details, status_code=400)


class NotFoundError(SeederBotException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(f"{resource} not found: {message}", details, status_code=404)
        self.resource = resource


class RateLimitError(SeederBotException):
    """Raised when rate limiting is triggered."""

    def __init__(self, message: str = "Rate limit exceeded", details: dict[str, Any] | None = None):
        super().__init__(message, details, status_code=429)
