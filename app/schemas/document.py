"""Document schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""

    document_id: str
    internal_id: str
    filename: str
    status: str
    created_at: datetime


class DocumentResponse(BaseModel):
    """Document details response."""

    id: str
    internal_id: str
    filename: str
    status: str
    document_type: str
    width: int | None = None
    height: int | None = None
    mrz_detected: bool
    created_at: datetime
    updated_at: datetime


class ExtractionResponse(BaseModel):
    """Extraction result response."""

    document_id: str
    mrz_detected: bool
    mrz_data: dict[str, Any] | None = None
    ocr_fields: dict[str, Any] = {}
    normalized_fields: dict[str, Any] = {}
    quality: dict[str, Any] | None = None
    ocr_engine_used: str | None = None
