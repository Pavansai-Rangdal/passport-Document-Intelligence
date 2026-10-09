"""API routes."""

from fastapi import APIRouter

from app.api.routes.batches import router as batches_router
from app.api.routes.decisions import router as decisions_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.uploads import router as uploads_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(uploads_router, prefix="/api/v1", tags=["uploads"])
api_router.include_router(documents_router, prefix="/api/v1", tags=["documents"])
api_router.include_router(batches_router, prefix="/api/v1", tags=["batches"])
api_router.include_router(decisions_router, prefix="/api/v1", tags=["decisions"])
