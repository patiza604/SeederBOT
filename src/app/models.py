import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class GrabRequest(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Movie title to search for"
    )
    type: Literal["movie"] = Field(
        default="movie",
        description="Content type"
    )
    year: int | None = Field(
        None,
        ge=1900,
        le=2030,
        description="Optional year to help disambiguation"
    )

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate and clean the movie title."""
        # Strip whitespace
        v = v.strip()

        # Check for empty string after stripping
        if not v:
            raise ValueError("Title cannot be empty")

        # Remove excessive whitespace
        v = re.sub(r'\s+', ' ', v)

        # Check for potentially malicious patterns
        if re.search(r'[<>\"\'&]', v):
            raise ValueError("Title contains invalid characters")

        return v

    @field_validator('year')
    @classmethod
    def validate_year(cls, v: int | None) -> int | None:
        """Validate the year if provided."""
        if v is not None:
            current_year = 2024  # Could be made dynamic
            if v > current_year + 5:
                raise ValueError("Year cannot be more than 5 years in the future")

        return v


class GrabResponse(BaseModel):
    status: str = Field(..., description="Success or error status")
    message: str = Field(..., description="Human readable message")
    details: dict | None = Field(None, description="Additional response details")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall health status: healthy, degraded, unhealthy")
    timestamp: float = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Service version")
    mode: str = Field(..., description="Current operation mode")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    duration_ms: float = Field(..., description="Health check duration in milliseconds")
    checks: dict[str, Any] = Field(..., description="Individual component health checks")


class SimpleHealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    mode: str = Field(..., description="Current operation mode")
    version: str = Field(..., description="Service version")

