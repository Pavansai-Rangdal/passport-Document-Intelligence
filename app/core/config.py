"""Application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Passport Expiry Classifier"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    host: str = "0.0.0.0"
    port: int = 8000

    # OCR
    ocr_engine: Literal["paddle", "tesseract", "both"] = "both"
    ocr_confidence_threshold: float = Field(default=0.7)

    # Image quality thresholds
    min_image_width: int = 800
    min_image_height: int = 600
    max_blur_score: float = 100.0
    min_brightness: float = 50.0
    max_brightness: float = 200.0

    # Laya (System One) ML model
    laya_api_url: str = Field(default="", description="Laya model API base URL")
    laya_api_key: str = Field(default="", description="Laya model API key")
    laya_timeout_seconds: int = 30

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "text"] = "json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
