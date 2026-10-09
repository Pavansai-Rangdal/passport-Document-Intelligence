"""Document endpoints."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import AuditLogger
from app.db.repositories import DocumentRepository
from app.db.session import get_session
from app.extraction import ExtractionService
from app.schemas import DocumentResponse, ExtractionResponse

router = APIRouter()


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> DocumentResponse:
    """Get document details."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID")

    doc_repo = DocumentRepository(session)
    document = await doc_repo.get_by_id(doc_uuid)

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return DocumentResponse(
        id=str(document.id),
        internal_id=document.internal_id,
        filename=document.filename,
        status=document.status.value,
        document_type=document.document_type.value,
        width=document.width,
        height=document.height,
        mrz_detected=document.mrz_detected,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.post("/documents/{document_id}/extract", response_model=ExtractionResponse)
async def extract_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> ExtractionResponse:
    """Extract data from a document."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID")

    doc_repo = DocumentRepository(session)
    document = await doc_repo.get_by_id(doc_uuid)

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Perform extraction
    extraction_service = ExtractionService()
    file_path = Path(document.file_path)

    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    try:
        extraction_data = extraction_service.extract_from_image(file_path)

        # Update document with extraction results
        if extraction_data.get("quality"):
            quality = extraction_data["quality"]
            await doc_repo.update_image_quality(
                document_id=doc_uuid,
                width=quality.get("width", 0),
                height=quality.get("height", 0),
                blur_score=quality.get("blur_score"),
                brightness=quality.get("brightness"),
                quality_passed=quality.get("quality_passed"),
            )

        if extraction_data.get("mrz_detected"):
            mrz_data = extraction_data.get("mrz_data")
            await doc_repo.update_mrz_info(
                document_id=doc_uuid,
                mrz_detected=True,
                mrz_type=mrz_data.get("mrz_type") if mrz_data else None,
            )

        # Update status
        from app.db.models import DocumentStatus

        await doc_repo.update_status(doc_uuid, DocumentStatus.EXTRACTED)

        await AuditLogger.log_document_processed(session=session, document_id=str(doc_uuid))
        await session.commit()

        return ExtractionResponse(
            document_id=str(document.id),
            mrz_detected=extraction_data.get("mrz_detected", False),
            mrz_data=extraction_data.get("mrz_data"),
            ocr_fields=extraction_data.get("ocr_fields", {}),
            normalized_fields=extraction_data.get("normalized_fields", {}),
            quality=extraction_data.get("quality"),
            ocr_engine_used=extraction_data.get("ocr_engine_used"),
        )
    except Exception as e:
        await doc_repo.update_status(doc_uuid, DocumentStatus.FAILED, error_message=str(e))
        await session.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
