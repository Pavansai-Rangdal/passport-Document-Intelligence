"""Health check endpoint."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas import HealthResponse

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )
