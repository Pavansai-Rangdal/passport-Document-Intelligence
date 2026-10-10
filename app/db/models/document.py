"""Document model for passport uploads."""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.batch import Batch
    from app.db.models.evidence import Evidence
    from app.db.models.passport_field import PassportField
    from app.db.models.validation_result import ValidationResult
    from app.db.models.verification_attempt import VerificationAttempt


class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    VALIDATED = "validated"
    FAILED = "failed"
    COMPLETED = "completed"


class DocumentType(str, Enum):
    """Document type."""
    PASSPORT_TD1 = "passport_td1"
    PASSPORT_TD2 = "passport_td2"
    PASSPORT_TD3 = "passport_td3"
    ID_CARD = "id_card"
    UNKNOWN = "unknown"


class Document(Base):
    """Represents an uploaded passport document."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    internal_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    batch_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("batches.id"), nullable=True, index=True)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.UPLOADED,
        nullable=False,
        index=True,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType),
        default=DocumentType.UNKNOWN,
        nullable=False,
    )

    # Image quality metrics
    width: Mapped[int | None] = mapped_column(nullable=True)
    height: Mapped[int | None] = mapped_column(nullable=True)
    dpi: Mapped[int | None] = mapped_column(nullable=True)
    blur_score: Mapped[float | None] = mapped_column(nullable=True)
    brightness: Mapped[float | None] = mapped_column(nullable=True)
    quality_passed: Mapped[bool | None] = mapped_column(nullable=True)

    # MRZ information
    mrz_detected: Mapped[bool] = mapped_column(default=False, nullable=False)
    mrz_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    mrz_lines: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Error information
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    batch: Mapped["Batch"] = relationship("Batch", back_populates="documents", lazy="selectin")
    fields: Mapped[list["PassportField"]] = relationship(
        "PassportField",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    validation_results: Mapped[list["ValidationResult"]] = relationship(
        "ValidationResult",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    evidence: Mapped[list["Evidence"]] = relationship(
        "Evidence",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    verification_attempts: Mapped[list["VerificationAttempt"]] = relationship(
        "VerificationAttempt",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
