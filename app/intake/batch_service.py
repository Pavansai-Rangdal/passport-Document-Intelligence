"""Batch service for grouping document uploads."""

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import FileIntakeError
from app.core.logging import get_logger
from app.db.repositories import BatchRepository, DocumentRepository
from app.intake.file_hashing import compute_file_hash
from app.intake.file_validator import FileValidator
from app.utils import generate_batch_id, generate_internal_id

logger = get_logger(__name__)


class BatchService:
    """Service for managing document batches."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.batch_repo = BatchRepository(session)
        self.document_repo = DocumentRepository(session)
        self.validator = FileValidator()

    async def create_batch(self, submitted_by: str | None = None) -> uuid.UUID:
        """Create a new batch."""
        internal_id = generate_batch_id()
        batch = await self.batch_repo.create(internal_id=internal_id, submitted_by=submitted_by)
        logger.info("Batch created", batch_id=str(batch.id), internal_id=internal_id)
        return batch.id

    async def add_document_to_batch(
        self,
        batch_id: uuid.UUID,
        file_path: Path,
        filename: str,
    ) -> uuid.UUID:
        """Add a document to a batch."""
        # Validate file
        self.validator.validate_file_integrity(file_path)
        file_size = file_path.stat().st_size
        self.validator.validate_file_size(file_size)
        mime_type = self.validator.validate_mime_type(file_path)
        self.validator.detect_malformed_file(file_path, mime_type)

        # Compute hash
        file_hash = compute_file_hash(file_path)

        # Check for duplicates
        existing = await self.document_repo.get_by_hash(file_hash)
        if existing:
            logger.warning("Duplicate file detected", file_hash=file_hash, existing_id=str(existing.id))
            raise FileIntakeError(f"Duplicate file detected (hash: {file_hash[:16]}...)")

        # Create document record
        internal_id = generate_internal_id()
        document = await self.document_repo.create(
            internal_id=internal_id,
            filename=filename,
            file_path=str(file_path),
            file_size=file_size,
            file_hash=file_hash,
            mime_type=mime_type,
            batch_id=batch_id,
        )

        # Update batch counters
        await self.batch_repo.increment_document_count(batch_id)

        logger.info("Document added to batch", document_id=str(document.id), batch_id=str(batch_id))
        return document.id

    async def get_batch(self, batch_id: uuid.UUID) -> dict[str, Any] | None:
        """Get batch details."""
        batch = await self.batch_repo.get_by_id(batch_id)
        if not batch:
            return None

        return {
            "id": str(batch.id),
            "internal_id": batch.internal_id,
            "status": batch.status.value,
            "total_documents": batch.total_documents,
            "processed_documents": batch.processed_documents,
            "failed_documents": batch.failed_documents,
            "submitted_by": batch.submitted_by,
            "submitted_at": batch.submitted_at.isoformat(),
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
        }
