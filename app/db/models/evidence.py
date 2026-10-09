"""Evidence model for verification evidence."""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.document import Document


class EvidenceType(str, Enum):
    """Types of evidence collected."""
    IMAGE_QUALITY = "image_quality"
    MRZ_DETECTED = "mrz_detected"
    OCR_EXTRACTION = "ocr_extraction"
    FIELD_CONSISTENCY = "field_consistency"
    VERIFICATION_ATTEMPT = "verification_attempt"
    SYSTEM_ONE_DECISION = "system_one_decision"
    POLICY_EVALUATION = "policy_evaluation"


class Evidence(Base):
    """Represents evidence collected during verification."""

    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(String(36), nullable=False, index=True)

    evidence_type: Mapped[EvidenceType] = mapped_column(SQLEnum(EvidenceType), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    timestamp: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="evidence")
