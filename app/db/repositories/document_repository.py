"""Document repository for database operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.db.models import Document, DocumentStatus, PassportField

logger = get_logger(__name__)


class DocumentRepository:
    """Repository for document CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        internal_id: str,
        filename: str,
        file_path: str,
        file_size: int,
        file_hash: str,
        mime_type: str,
        batch_id: uuid.UUID | None = None,
    ) -> Document:
        """Create a new document record."""
        document = Document(
            internal_id=internal_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            mime_type=mime_type,
            batch_id=str(batch_id) if batch_id else None,
        )
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)
        logger.info("Document created", document_id=str(document.id), internal_id=internal_id)
        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        """Get document by ID with relationships."""
        stmt = (
            select(Document)
            .where(Document.id == document_id)
            .options(
                selectinload(Document.fields),
                selectinload(Document.validation_results),
                selectinload(Document.evidence),
                selectinload(Document.verification_attempts),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_internal_id(self, internal_id: str) -> Document | None:
        """Get document by internal ID."""
        stmt = select(Document).where(Document.internal_id == internal_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_hash(self, file_hash: str) -> Document | None:
        """Get document by file hash."""
        stmt = select(Document).where(Document.file_hash == file_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStatus,
        error_message: str | None = None,
    ) -> Document | None:
        """Update document status."""
        document = await self.get_by_id(document_id)
        if document:
            document.status = status
            if error_message:
                document.error_message = error_message
            await self.session.flush()
            await self.session.refresh(document)
            logger.info("Document status updated", document_id=str(document_id), status=status.value)
        return document

    async def update_image_quality(
        self,
        document_id: uuid.UUID,
        width: int,
        height: int,
        dpi: int | None = None,
        blur_score: float | None = None,
        brightness: float | None = None,
        quality_passed: bool | None = None,
    ) -> Document | None:
        """Update document image quality metrics."""
        document = await self.get_by_id(document_id)
        if document:
            document.width = width
            document.height = height
            document.dpi = dpi
            document.blur_score = blur_score
            document.brightness = brightness
            document.quality_passed = quality_passed
            await self.session.flush()
            await self.session.refresh(document)
        return document

    async def update_mrz_info(
        self,
        document_id: uuid.UUID,
        mrz_detected: bool,
        mrz_type: str | None = None,
        mrz_lines: str | None = None,
    ) -> Document | None:
        """Update document MRZ information."""
        document = await self.get_by_id(document_id)
        if document:
            document.mrz_detected = mrz_detected
            document.mrz_type = mrz_type
            document.mrz_lines = mrz_lines
            await self.session.flush()
            await self.session.refresh(document)
        return document

    async def add_field(
        self,
        document_id: uuid.UUID,
        field_type: str,
        field_name: str,
        value: str,
        source: str,
        confidence: float | None = None,
        ocr_engine: str | None = None,
        value_normalized: str | None = None,
    ) -> PassportField:
        """Add an extracted field to a document."""
        field = PassportField(
            document_id=str(document_id),
            field_type=field_type,
            field_name=field_name,
            value=value,
            value_normalized=value_normalized,
            source=source,
            confidence=confidence,
            ocr_engine=ocr_engine,
        )
        self.session.add(field)
        await self.session.flush()
        await self.session.refresh(field)
        return field

    async def delete(self, document_id: uuid.UUID) -> bool:
        """Delete a document."""
        document = await self.get_by_id(document_id)
        if document:
            await self.session.delete(document)
            await self.session.flush()
            logger.info("Document deleted", document_id=str(document_id))
            return True
        return False
