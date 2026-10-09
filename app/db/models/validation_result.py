"""Validation result model for rule checks."""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.document import Document


class RuleCategory(str, Enum):
    """Categories of validation rules."""
    SCHEMA = "schema"
    EXPIRY = "expiry"
    IMAGE_QUALITY = "image_quality"
    CROSS_FIELD = "cross_field"
    MRZ_CHECKSUM = "mrz_checksum"
    CONSISTENCY = "consistency"


class ValidationSeverity(str, Enum):
    """Severity levels for validation failures."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationResult(Base):
    """Represents a validation rule check result."""

    __tablename__ = "validation_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(String(36), nullable=False, index=True)

    rule_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    rule_category: Mapped[RuleCategory] = mapped_column(SQLEnum(RuleCategory), nullable=False)
    severity: Mapped[ValidationSeverity] = mapped_column(SQLEnum(ValidationSeverity), nullable=False)

    passed: Mapped[bool] = mapped_column(nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="validation_results")
