"""Batch model for grouping document uploads."""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.decision_record import DecisionRecord
    from app.db.models.document import Document


class BatchStatus(str, Enum):
    """Batch processing status."""
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class Batch(Base):
    """Represents a batch of uploaded documents."""

    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    internal_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    status: Mapped[BatchStatus] = mapped_column(
        SQLEnum(BatchStatus),
        default=BatchStatus.CREATED,
        nullable=False,
        index=True,
    )

    total_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    submitted_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="batch",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    decisions: Mapped[list["DecisionRecord"]] = relationship(
        "DecisionRecord",
        back_populates="batch",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
