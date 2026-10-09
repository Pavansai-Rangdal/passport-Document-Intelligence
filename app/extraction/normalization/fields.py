"""Field normalization utilities."""

import re

from app.core.logging import get_logger

logger = get_logger(__name__)


class FieldNormalizer:
    """Normalizes extracted passport fields."""

    @staticmethod
    def normalize_document_number(value: str) -> str:
        """Normalize document number."""
        if not value:
            return ""
        # Remove spaces and special characters, keep alphanumeric
        normalized = re.sub(r"[^A-Z0-9<]", "", value.upper())
        return normalized

    @staticmethod
    def normalize_name(value: str) -> str:
        """Normalize name fields."""
        if not value:
            return ""
        # Convert to title case, replace special characters
        normalized = re.sub(r"[^A-Z\s]", "", value.upper())
        # Replace multiple spaces with single space
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    @staticmethod
    def normalize_country_code(value: str) -> str:
        """Normalize 3-letter country code."""
        if not value:
            return ""
        # Convert to uppercase, ensure 3 letters
        normalized = re.sub(r"[^A-Z]", "", value.upper())
        return normalized[:3]

    @staticmethod
    def normalize_sex(value: str) -> str:
        """Normalize sex field (M/F)."""
        if not value:
            return ""
        normalized = value.upper().strip()
        if normalized in ("M", "MALE"):
            return "M"
        elif normalized in ("F", "FEMALE"):
            return "F"
        elif normalized in ("X", "UNSPECIFIED"):
            return "X"
        return ""

    @staticmethod
    def normalize_numeric(value: str) -> str:
        """Normalize numeric fields."""
        if not value:
            return ""
        normalized = re.sub(r"[^0-9]", "", value)
        return normalized

    @staticmethod
    def clean_whitespace(value: str) -> str:
        """Clean up whitespace in field values."""
        if not value:
            return ""
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def remove_fillers(value: str) -> str:
        """Remove MRZ filler characters (<)."""
        if not value:
            return ""
        return value.replace("<", " ").strip()
