"""Decision record model for final verification decisions."""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.batch import Batch


class DecisionOutcome(str, Enum):
    """Final decision outcomes."""
    PASS_SCREENING = "pass_screening"
    FAIL_RULE = "fail_rule"
    REVIEW_REQUIRED = "review_required"
    INSUFFICIENT_DATA = "insufficient_data"


class DecisionRecord(Base):
    """Represents a final verification decision."""

    __tablename__ = "decision_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(String(36), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(String(36), nullable=False, index=True)

    outcome: Mapped[DecisionOutcome] = mapped_column(SQLEnum(DecisionOutcome), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(nullable=False)

    # System One recommendation
    system_one_recommendation: Mapped[str | None] = mapped_column(String(50), nullable=True)
    system_one_confidence: Mapped[float | None] = mapped_column(nullable=True)

    # Policy engine result
    policy_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    policy_rules_triggered: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    batch: Mapped["Batch"] = relationship("Batch", back_populates="decisions")
