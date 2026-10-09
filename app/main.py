"""FastAPI application main entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import api_router
from app.core import configure_logging, get_logger, get_settings
from app.db import close_db, init_db

settings = get_settings()
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    try:
        await init_db()
    except Exception as e:
        settings = get_settings()
        if settings.environment == "development":
            logger.warning("Database initialization failed, continuing without database", error=str(e))
        else:
            raise
    yield
    # Shutdown
    try:
        await close_db()
    except Exception:
        pass


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A secure document-intelligence pipeline for passport image extraction, validation, and evidence-based decisions.",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }
