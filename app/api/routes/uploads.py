"""Upload endpoints."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import AuditLogger
from app.core.config import get_settings
from app.core.exceptions import FileIntakeError
from app.db.repositories import DocumentRepository
from app.db.session import get_session
from app.intake import BatchService
from app.schemas import DocumentUploadResponse

router = APIRouter()
settings = get_settings()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    batch_id: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> DocumentUploadResponse:
    """Upload a passport document for processing."""
    # Validate file size
    content = await file.read()
    file_size = len(content)

    if file_size > settings.storage_max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum of {settings.storage_max_file_size} bytes",
        )

    # Create storage path
    storage_path = settings.storage_path
    storage_path.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = storage_path / unique_filename

    # Save file
    file_path.write_bytes(content)

    # Create or get batch
    batch_service = BatchService(session)
    if batch_id:
        # Add to existing batch
        # For now, create new batch if batch_id not found
        try:
            batch_uuid = await batch_service.create_batch()
        except Exception:
            batch_uuid = await batch_service.create_batch()
    else:
        batch_uuid = await batch_service.create_batch()

    # Add document to batch
    try:
        document_uuid = await batch_service.add_document_to_batch(
            batch_id=batch_uuid,
            file_path=file_path,
            filename=file.filename,
        )
    except FileIntakeError as e:
        # Clean up file if validation fails
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Get document details
    doc_repo = DocumentRepository(session)
    document = await doc_repo.get_by_id(document_uuid)

    await AuditLogger.log_document_uploaded(
        session=session,
        document_id=str(document.id),
        filename=document.filename,
    )
    await session.commit()

    return DocumentUploadResponse(
        document_id=str(document.id),
        internal_id=document.internal_id,
        filename=document.filename,
        status=document.status.value,
        created_at=document.created_at,
    )
