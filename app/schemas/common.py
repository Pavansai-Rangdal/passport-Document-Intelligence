"""Common schema definitions."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: str | None = None
