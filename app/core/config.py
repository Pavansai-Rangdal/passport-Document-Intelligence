"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Passport Document Intelligence"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/passport_db",
        description="PostgreSQL database URL",
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching and Celery broker",
    )

    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL",
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL",
    )

    # Storage
    storage_path: Path = Field(default=Path("data/uploads"), description="Upload storage path")
    storage_max_file_size: int = Field(default=10 * 1024 * 1024, description="Max file size in bytes (10MB)")
    storage_allowed_mime_types: list[str] = Field(
        default=[
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/webp",
            "application/pdf",
        ],
        description="Allowed MIME types for uploads",
    )

    # Retention
    retention_days: int = Field(default=90, description="Days to retain uploaded files")
    retention_audit_days: int = Field(default=365, description="Days to retain audit logs")

    # OCR Configuration
    ocr_engine: Literal["paddle", "tesseract", "both"] = Field(
        default="both",
        description="OCR engine to use",
    )
    ocr_confidence_threshold: float = Field(default=0.7, description="Minimum OCR confidence threshold")

    # Security
    secret_key: str = Field(default="change-me-in-production", description="Secret key for signing")
    encryption_key: str = Field(default="change-me-in-production", description="Encryption key for sensitive data")
    max_upload_rate: int = Field(default=10, description="Max uploads per minute per IP")
    api_key_required: bool = False

    # Verification
    enable_chip_authentication: bool = False
    enable_lost_stolen_check: bool = False
    verification_timeout_seconds: int = 30

    # System One Integration
    system_one_enabled: bool = False
    system_one_api_url: str = ""
    system_one_api_key: str = ""
    system_one_timeout_seconds: int = 30

    # Processing
    batch_size: int = Field(default=50, description="Max documents per batch")
    processing_timeout_seconds: int = Field(default=300, description="Max processing time per document")

    # Quality thresholds
    min_image_width: int = 800
    min_image_height: int = 600
    min_dpi: int = 150
    max_blur_score: float = 100.0
    min_brightness: float = 50.0
    max_brightness: float = 200.0

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    @field_validator("storage_path")
    @classmethod
    def validate_storage_path(cls, v: Path) -> Path:
        """Ensure storage path exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses asyncpg driver."""
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("Database URL must use postgresql+asyncpg:// driver")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
