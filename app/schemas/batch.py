"""Batch schemas."""

from datetime import datetime

from pydantic import BaseModel


class BatchCreateResponse(BaseModel):
    """Response for batch creation."""

    batch_id: str
    internal_id: str
    status: str
    created_at: datetime


class BatchResponse(BaseModel):
    """Batch details response."""

    id: str
    internal_id: str
    status: str
    total_documents: int
    processed_documents: int
    failed_documents: int
    submitted_by: str | None = None
    submitted_at: datetime
    completed_at: datetime | None = None
