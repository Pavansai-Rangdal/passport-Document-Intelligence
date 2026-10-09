"""Retention policy management."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import AuditEvent, Document, DocumentStatus

logger = get_logger(__name__)

settings = get_settings()


class RetentionManager:
    """Manages data retention policies."""

    @staticmethod
    async def cleanup_expired_documents(session: AsyncSession) -> dict[str, Any]:
        """Clean up documents past retention period."""
        cutoff_date = datetime.utcnow() - timedelta(days=settings.retention_days)

        # Find documents past retention
        stmt = select(Document).where(
            Document.created_at < cutoff_date,
            Document.status.in_(
                [DocumentStatus.COMPLETED, DocumentStatus.FAILED]
            ),
        )
        result = await session.execute(stmt)
        documents = result.scalars().all()

        deleted_count = 0
        errors = []

        for document in documents:
            try:
                # Delete file
                file_path = Path(document.file_path)
                if file_path.exists():
                    file_path.unlink()

                # Delete database record
                await session.delete(document)
                deleted_count += 1

                logger.info("Document expired and deleted", document_id=str(document.id))
            except Exception as e:
                errors.append(str(e))
                logger.error("Failed to delete expired document", document_id=str(document.id), error=str(e))

        await session.commit()

        return {
            "deleted_count": deleted_count,
            "errors": errors,
            "cutoff_date": cutoff_date.isoformat(),
        }

    @staticmethod
    async def cleanup_old_audit_logs(session: AsyncSession) -> dict[str, Any]:
        """Clean up audit logs past retention period."""
        cutoff_date = datetime.utcnow() - timedelta(days=settings.retention_audit_days)

        stmt = select(AuditEvent).where(AuditEvent.created_at < cutoff_date)
        result = await session.execute(stmt)
        events = result.scalars().all()

        deleted_count = len(events)

        for event in events:
            await session.delete(event)

        await session.commit()

        logger.info("Old audit logs cleaned up", count=deleted_count, cutoff_date=cutoff_date.isoformat())

        return {
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
        }

    @staticmethod
    async def get_retention_stats(session: AsyncSession) -> dict[str, Any]:
        """Get retention statistics."""
        from sqlalchemy import func

        # Count documents by age
        cutoff_date = datetime.utcnow() - timedelta(days=settings.retention_days)

        total_stmt = select(func.count(Document.id))
        total_result = await session.execute(total_stmt)
        total_documents = total_result.scalar()

        expired_stmt = select(func.count(Document.id)).where(Document.created_at < cutoff_date)
        expired_result = await session.execute(expired_stmt)
        expired_documents = expired_result.scalar()

        # Count audit logs
        audit_cutoff = datetime.utcnow() - timedelta(days=settings.retention_audit_days)
        audit_stmt = select(func.count(AuditEvent.id)).where(AuditEvent.created_at < audit_cutoff)
        audit_result = await session.execute(audit_stmt)
        expired_audit_logs = audit_result.scalar()

        return {
            "total_documents": total_documents,
            "expired_documents": expired_documents,
            "expired_audit_logs": expired_audit_logs,
            "document_retention_days": settings.retention_days,
            "audit_retention_days": settings.retention_audit_days,
        }
