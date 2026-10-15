"""Field extraction from OCR results."""

import re
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

# OCR digit-correction map (same substitutions as MRZParser)
_DIGIT_MAP = str.maketrans({"O": "0", "Q": "0", "I": "1", "L": "1", "Z": "2",
                             "E": "3", "A": "4", "S": "5", "G": "6", "B": "8",
                             "R": "8", "T": "7"})


def _mrz_date_plausible(date6: str) -> bool:
    """Return True if a 6-char MRZ date field (YYMMDD) looks valid after OCR correction."""
    corrected = date6.translate(_DIGIT_MAP)
    if not corrected.isdigit():
        return False
    month = int(corrected[2:4])
    day = int(corrected[4:6])
    return 1 <= month <= 12 and 1 <= day <= 31


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
        text = text.replace("\x00", "\n")
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
        """Extract MRZ lines from OCR text.

        Two-pass strategy:
        1. Fast path — look for lines that are already exactly 30/36/44 chars of valid MRZ chars.
        2. Fallback — collapse ALL MRZ-valid characters across the whole text into one stream
           and search for the TD3 two-line pattern (44+44) or TD1 three-line pattern (30×3).
        """
        valid = re.compile(r'^[A-Z0-9<]+$')
        lengths = {30, 36, 44}

        # Split into MRZ-zone section (before \x00 sentinel) and full-page section.
        # OCR engines put the MRZ-crop text first so the stream scan stays focused.
        mrz_section, _, full_section = text.partition("\x00")

        # Pass 1: prefer MRZ-zone lines; fall back to full-page lines if needed
        candidates: list[str] = []
        for scan_text in ([mrz_section, full_section] if full_section else [mrz_section]):
            for line in scan_text.split("\n"):
                cleaned = re.sub(r'\s+', '', line.strip().upper())
                if len(cleaned) in lengths and valid.match(cleaned):
                    candidates.append(cleaned)

        # Validate TD3 pairs: line2 must have a sex char at pos 20 and a plausible expiry date
        td3 = [l for l in candidates if len(l) == 44]
        for i in range(len(td3) - 1):
            line2 = td3[i + 1]
            if line2[20] in "MFX<" and _mrz_date_plausible(line2[21:27]):
                logger.info("MRZ lines extracted", count=2)
                return [td3[i], td3[i + 1]]

        # Validate TD1 triples (3 × 30 chars) per ICAO Doc 9303 Part 5:
        # line2 sex char at position 7, expiry date at positions 8-13.
        td1 = [l for l in candidates if len(l) == 30]
        for i in range(len(td1) - 2):
            line2 = td1[i + 1]
            if line2[7] in "MFX<" and _mrz_date_plausible(line2[8:14]):
                logger.info("MRZ lines extracted", count=3)
                return [td1[i], td1[i + 1], td1[i + 2]]

        # Validate TD2 pairs (2 × 36 chars) per ICAO Doc 9303 Part 6:
        # line2 sex char at position 20, expiry date at positions 21-26.
        td2 = [l for l in candidates if len(l) == 36]
        for i in range(len(td2) - 1):
            line2 = td2[i + 1]
            if line2[20] in "MFX<" and _mrz_date_plausible(line2[21:27]):
                logger.info("MRZ lines extracted", count=2)
                return [td2[i], td2[i + 1]]

        # Pass 2: stream scan — try MRZ-zone section first to avoid false positives,
        # then fall back to full text if nothing found.
        scan_sections = [mrz_section, mrz_section + full_section] if full_section else [mrz_section]

        for scan_text in scan_sections:
            stream = re.sub(r'[^A-Z0-9<]', '', scan_text.upper())

            # TD3 — strict (P prefix) then relaxed (any doc type), both require sex char.
            # Issuing state uses [A-Z<]{3} because some countries (e.g. Germany "D<<")
            # pad their single-letter code with < fillers.
            for td3_pat in [
                r'(P[<A-Z][A-Z<]{3}[A-Z0-9<]{39})([A-Z0-9<]{20}[MFX<][A-Z0-9<]{23})',
                r'([A-Z][<A-Z][A-Z<]{3}[A-Z0-9<]{39})([A-Z0-9<]{20}[MFX<][A-Z0-9<]{23})',
            ]:
                m = re.search(td3_pat, stream)
                if m and _mrz_date_plausible(m.group(2)[21:27]):
                    mrz_lines = [m.group(1), m.group(2)]
                    logger.info("MRZ lines extracted (stream scan)", count=len(mrz_lines))
                    return mrz_lines

            # TD2 — two lines of 36, sex char at position 20 of line 2
            m2 = re.search(r'([A-Z0-9<]{36})([A-Z0-9<]{20}[MFX<][A-Z0-9<]{15})', stream)
            if m2 and _mrz_date_plausible(m2.group(2)[21:27]):
                mrz_lines = [m2.group(1), m2.group(2)]
                logger.info("MRZ lines extracted (stream scan TD2)", count=len(mrz_lines))
                return mrz_lines

            # TD1 — three lines of 30, sex char at position 7 of line 2 per ICAO Doc 9303 Part 5
            m1 = re.search(r'([A-Z0-9<]{30})([A-Z0-9<]{7}[MFX<][A-Z0-9<]{22})([A-Z0-9<]{30})', stream)
            if m1 and _mrz_date_plausible(m1.group(2)[8:14]):
                mrz_lines = [m1.group(1), m1.group(2), m1.group(3)]
                logger.info("MRZ lines extracted (stream scan TD1)", count=len(mrz_lines))
                return mrz_lines

        logger.info("MRZ lines extracted", count=0)
        return []
