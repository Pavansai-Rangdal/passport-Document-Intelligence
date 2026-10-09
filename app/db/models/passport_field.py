"""Passport field model for extracted data."""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.document import Document


class FieldType(str, Enum):
    """Types of passport fields."""
    SURNAME = "surname"
    GIVEN_NAMES = "given_names"
    DOCUMENT_NUMBER = "document_number"
    NATIONALITY = "nationality"
    BIRTH_DATE = "birth_date"
    SEX = "sex"
    EXPIRY_DATE = "expiry_date"
    ISSUING_STATE = "issuing_state"
    PERSONAL_NUMBER = "personal_number"
    PLACE_OF_BIRTH = "place_of_birth"
    ISSUE_DATE = "issue_date"


class FieldSource(str, Enum):
    """Source of field extraction."""
    MRZ = "mrz"
    OCR_VIZ = "ocr_viz"
    OCR_MRZ = "ocr_mrz"
    MANUAL = "manual"


class PassportField(Base):
    """Represents an extracted passport field."""

    __tablename__ = "passport_fields"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(String(36), nullable=False, index=True)

    field_type: Mapped[FieldType] = mapped_column(SQLEnum(FieldType), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_normalized: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped[FieldSource] = mapped_column(SQLEnum(FieldSource), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    ocr_engine: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="fields")
