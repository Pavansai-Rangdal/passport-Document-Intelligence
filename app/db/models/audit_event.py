"""Audit event model for compliance logging."""

import uuid
from enum import Enum

from sqlalchemy import JSON, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EventType(str, Enum):
    """Types of audit events."""
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_PROCESSED = "document_processed"
    EXTRACTION_COMPLETED = "extraction_completed"
    VALIDATION_COMPLETED = "validation_completed"
    VERIFICATION_ATTEMPTED = "verification_attempted"
    DECISION_MADE = "decision_made"
    BATCH_CREATED = "batch_created"
    BATCH_COMPLETED = "batch_completed"
    ERROR_OCCURRED = "error_occurred"
    SECURITY_ALERT = "security_alert"


class AuditEvent(Base):
    """Represents an audit event for compliance."""

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    event_type: Mapped[EventType] = mapped_column(SQLEnum(EventType), nullable=False, index=True)
    actor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    action: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    success: Mapped[bool] = mapped_column(nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
