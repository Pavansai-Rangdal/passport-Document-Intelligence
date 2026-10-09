"""Batch repository for database operations."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.db.models import Batch, BatchStatus

logger = get_logger(__name__)


class BatchRepository:
    """Repository for batch CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        internal_id: str,
        submitted_by: str | None = None,
    ) -> Batch:
        """Create a new batch."""
        batch = Batch(
            internal_id=internal_id,
            submitted_by=submitted_by,
            submitted_at=datetime.utcnow(),
        )
        self.session.add(batch)
        await self.session.flush()
        await self.session.refresh(batch)
        logger.info("Batch created", batch_id=str(batch.id), internal_id=internal_id)
        return batch

    async def get_by_id(self, batch_id: uuid.UUID) -> Batch | None:
        """Get batch by ID with relationships."""
        stmt = (
            select(Batch)
            .where(Batch.id == batch_id)
            .options(
                selectinload(Batch.documents),
                selectinload(Batch.decisions),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_internal_id(self, internal_id: str) -> Batch | None:
        """Get batch by internal ID."""
        stmt = select(Batch).where(Batch.internal_id == internal_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        batch_id: uuid.UUID,
        status: BatchStatus,
        completed_at: datetime | None = None,
    ) -> Batch | None:
        """Update batch status."""
        batch = await self.get_by_id(batch_id)
        if batch:
            batch.status = status
            if completed_at:
                batch.completed_at = completed_at
            await self.session.flush()
            await self.session.refresh(batch)
            logger.info("Batch status updated", batch_id=str(batch_id), status=status.value)
        return batch

    async def increment_document_count(
        self,
        batch_id: uuid.UUID,
        increment_processed: bool = False,
        increment_failed: bool = False,
    ) -> Batch | None:
        """Increment document counters for a batch."""
        batch = await self.get_by_id(batch_id)
        if batch:
            batch.total_documents += 1
            if increment_processed:
                batch.processed_documents += 1
            if increment_failed:
                batch.failed_documents += 1
            await self.session.flush()
            await self.session.refresh(batch)
        return batch

    async def delete(self, batch_id: uuid.UUID) -> bool:
        """Delete a batch."""
        batch = await self.get_by_id(batch_id)
        if batch:
            await self.session.delete(batch)
            await self.session.flush()
            logger.info("Batch deleted", batch_id=str(batch_id))
            return True
        return False
