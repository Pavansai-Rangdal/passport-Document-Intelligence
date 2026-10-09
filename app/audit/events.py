"""Audit event logging."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import AuditEvent, EventType

logger = get_logger(__name__)


class AuditLogger:
    """Logs audit events for compliance."""

    @staticmethod
    async def log_event(
        session: AsyncSession,
        event_type: EventType,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        actor: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> AuditEvent:
        """Log an audit event."""
        event = AuditEvent(
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor=actor,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )

        session.add(event)
        await session.flush()
        await session.refresh(event)

        logger.info(
            "Audit event logged",
            event_type=event_type.value,
            action=action,
            success=success,
        )

        return event

    @staticmethod
    async def log_document_uploaded(
        session: AsyncSession,
        document_id: str,
        filename: str,
        actor: str | None = None,
        ip_address: str | None = None,
    ) -> AuditEvent:
        """Log document upload event."""
        return await AuditLogger.log_event(
            session=session,
            event_type=EventType.DOCUMENT_UPLOADED,
            action="document_uploaded",
            resource_type="document",
            resource_id=document_id,
            actor=actor,
            ip_address=ip_address,
            details={"filename": filename},
            success=True,
        )

    @staticmethod
    async def log_document_processed(
        session: AsyncSession,
        document_id: str,
        actor: str | None = None,
    ) -> AuditEvent:
        """Log document processing event."""
        return await AuditLogger.log_event(
            session=session,
            event_type=EventType.DOCUMENT_PROCESSED,
            action="document_processed",
            resource_type="document",
            resource_id=document_id,
            actor=actor,
            success=True,
        )

    @staticmethod
    async def log_decision_made(
        session: AsyncSession,
        document_id: str,
        outcome: str,
        actor: str | None = None,
    ) -> AuditEvent:
        """Log decision event."""
        return await AuditLogger.log_event(
            session=session,
            event_type=EventType.DECISION_MADE,
            action="decision_made",
            resource_type="document",
            resource_id=document_id,
            actor=actor,
            details={"outcome": outcome},
            success=True,
        )

    @staticmethod
    async def log_error(
        session: AsyncSession,
        action: str,
        error_message: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> AuditEvent:
        """Log error event."""
        return await AuditLogger.log_event(
            session=session,
            event_type=EventType.ERROR_OCCURRED,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            error_message=error_message,
            success=False,
        )
