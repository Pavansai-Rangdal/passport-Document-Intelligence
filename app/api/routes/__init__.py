"""API routes."""

from fastapi import APIRouter

from app.api.routes.classify import router as classify_router
from app.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(classify_router, prefix="/api/v1", tags=["classify"])
