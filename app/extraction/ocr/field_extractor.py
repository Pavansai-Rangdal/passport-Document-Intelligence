"""Field extraction from OCR results."""

import re
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class FieldExtractor:
    """Extracts specific passport fields from OCR text."""

    # Common patterns for passport fields
    PATTERNS = {
        "document_number": r"[A-Z]{1,2}\d{6,9}",
        "passport_number": r"[A-Z]{1,2}\d{6,9}",
        "surname": r"Surname\s*[:/]?\s*([A-Z\s]+)",
        "given_names": r"Given\s*names?\s*[:/]?\s*([A-Z\s]+)",
        "nationality": r"Nationality\s*[:/]?\s*([A-Z]{3})",
        "birth_date": r"Date\s*of\s*birth\s*[:/]?\s*(\d{2}[\./]\d{2}[\./]\d{4})",
        "sex": r"Sex\s*[:/]?\s*([MF])",
        "expiry_date": r"Date\s*of\s*expiry\s*[:/]?\s*(\d{2}[\./]\d{2}[\./]\d{4})",
        "issuing_state": r"Place\s*of\s*issue\s*[:/]?\s*([A-Z]{3})",
        "place_of_birth": r"Place\s*of\s*birth\s*[:/]?\s*([A-Z\s,]+)",
    }

    @staticmethod
    def extract_fields(text: str) -> dict[str, Any]:
        """Extract passport fields from OCR text."""
        extracted = {}

        for field_name, pattern in FieldExtractor.PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip() if match.groups() else match.group(0).strip()
                extracted[field_name] = value
                logger.debug("Field extracted", field=field_name, value=value[:20])

        logger.info("Fields extracted from OCR", count=len(extracted))
        return extracted

    @staticmethod
    def extract_mrz_lines(text: str) -> list[str]:
        """Extract MRZ lines from text."""
        lines = text.split("\n")
        mrz_lines = []

        for line in lines:
            cleaned = line.strip().upper()
            # MRZ lines are typically 30 or 44 characters
            if len(cleaned) in (30, 44) and cleaned.isalnum():
                mrz_lines.append(cleaned)

        logger.info("MRZ lines extracted", count=len(mrz_lines))
        return mrz_lines
