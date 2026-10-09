"""Batch endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import BatchRepository
from app.db.session import get_session
from app.intake import BatchService
from app.reporting.batch_report import BatchReportGenerator
from app.schemas import BatchCreateResponse, BatchResponse

router = APIRouter()


@router.post("/batches", response_model=BatchCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    submitted_by: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> BatchCreateResponse:
    """Create a new batch for document uploads."""
    batch_service = BatchService(session)
    batch_uuid = await batch_service.create_batch(submitted_by=submitted_by)

    batch_repo = BatchRepository(session)
    batch = await batch_repo.get_by_id(batch_uuid)
    if not batch:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create batch")

    return BatchCreateResponse(
        batch_id=str(batch.id),
        internal_id=batch.internal_id,
        status=batch.status.value,
        created_at=batch.submitted_at,
    )


@router.get("/batches/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: str,
    session: AsyncSession = Depends(get_session),
) -> BatchResponse:
    """Get batch details."""
    try:
        batch_uuid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid batch ID")

    batch_repo = BatchRepository(session)
    batch = await batch_repo.get_by_id(batch_uuid)

    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    return BatchResponse(
        id=str(batch.id),
        internal_id=batch.internal_id,
        status=batch.status.value,
        total_documents=batch.total_documents,
        processed_documents=batch.processed_documents,
        failed_documents=batch.failed_documents,
        submitted_by=batch.submitted_by,
        submitted_at=batch.submitted_at,
        completed_at=batch.completed_at,
    )


@router.get("/batches/{batch_id}/report")
async def get_batch_report(
    batch_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get a full report for a batch including per-document outcomes."""
    try:
        uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid batch ID")

    try:
        report = await BatchReportGenerator.generate_batch_report(session, batch_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    return report
