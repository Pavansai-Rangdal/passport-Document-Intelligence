"""Batch report generation."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import Batch, DecisionRecord, Document

logger = get_logger(__name__)


class BatchReportGenerator:
    """Generates reports for document batches."""

    @staticmethod
    async def generate_batch_report(session: AsyncSession, batch_id: str) -> dict[str, Any]:
        """Generate a comprehensive report for a batch."""
        import uuid

        batch_uuid = uuid.UUID(batch_id)

        # Get batch
        stmt = select(Batch).where(Batch.id == batch_uuid)
        result = await session.execute(stmt)
        batch = result.scalar_one_or_none()

        if not batch:
            raise ValueError(f"Batch not found: {batch_id}")

        # Get documents
        doc_stmt = select(Document).where(Document.batch_id == str(batch_uuid))
        doc_result = await session.execute(doc_stmt)
        documents = doc_result.scalars().all()

        # Get decisions
        decision_stmt = select(DecisionRecord).where(DecisionRecord.batch_id == str(batch_uuid))
        decision_result = await session.execute(decision_stmt)
        decisions = decision_result.scalars().all()

        # Calculate statistics
        total_docs = len(documents)
        status_counts = {}
        for doc in documents:
            status = doc.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        outcome_counts = {}
        for decision in decisions:
            outcome = decision.outcome.value
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1

        report = {
            "batch_id": str(batch.id),
            "internal_id": batch.internal_id,
            "status": batch.status.value,
            "submitted_at": batch.submitted_at.isoformat(),
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            "statistics": {
                "total_documents": total_docs,
                "processed_documents": batch.processed_documents,
                "failed_documents": batch.failed_documents,
                "status_breakdown": status_counts,
                "outcome_breakdown": outcome_counts,
            },
            "documents": [
                {
                    "id": str(doc.id),
                    "internal_id": doc.internal_id,
                    "filename": doc.filename,
                    "status": doc.status.value,
                    "mrz_detected": doc.mrz_detected,
                }
                for doc in documents
            ],
            "decisions": [
                {
                    "document_id": str(dec.document_id),
                    "outcome": dec.outcome.value,
                    "confidence": dec.confidence,
                }
                for dec in decisions
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }

        logger.info("Batch report generated", batch_id=batch_id)
        return report
