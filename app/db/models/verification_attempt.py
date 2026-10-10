"""Verification attempt model for external verifications."""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.document import Document


class VerificationProvider(str, Enum):
    """External verification providers."""
    SYSTEM_ONE = "system_one"
    ISSUER_DATABASE = "issuer_database"
    LOST_STOLEN_DATABASE = "lost_stolen_database"
    CHIP_AUTHENTICATION = "chip_authentication"


class VerificationStatus(str, Enum):
    """Status of verification attempts."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"


class VerificationAttempt(Base):
    """Represents an external verification attempt."""

    __tablename__ = "verification_attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)

    provider: Mapped[VerificationProvider] = mapped_column(SQLEnum(VerificationProvider), nullable=False)
    status: Mapped[VerificationStatus] = mapped_column(SQLEnum(VerificationStatus), nullable=False)

    request_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="verification_attempts")
