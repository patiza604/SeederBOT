from typing import Literal

from pydantic import BaseModel, Field


class GrabRequest(BaseModel):
    title: str = Field(..., description="Movie title to search for")
    type: Literal["movie"] = Field(default="movie", description="Content type")
    year: int | None = Field(None, description="Optional year to help disambiguation")


class GrabResponse(BaseModel):
    status: str = Field(..., description="Success or error status")
    message: str = Field(..., description="Human readable message")
    details: dict | None = Field(None, description="Additional response details")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    mode: str = Field(..., description="Current operation mode")
    version: str = Field(..., description="Service version")

