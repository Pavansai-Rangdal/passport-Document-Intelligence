"""MRZ parser for ICAO Doc 9303 compliant formats."""

from dataclasses import dataclass
from typing import Any

from app.core.exceptions import MRZError
from app.core.logging import get_logger
from app.extraction.mrz.check_digits import MRZCheckDigitValidator

logger = get_logger(__name__)


@dataclass
class MRZData:
    """Parsed MRZ data."""

    document_type: str
    issuing_state: str
    document_number: str
    birth_date: str
    expiry_date: str
    sex: str
    surname: str = ""
    given_names: str = ""
    nationality: str = ""
    personal_number: str = ""
    mrz_type: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_type": self.document_type,
            "issuing_state": self.issuing_state,
            "document_number": self.document_number,
            "birth_date": self.birth_date,
            "expiry_date": self.expiry_date,
            "sex": self.sex,
            "surname": self.surname,
            "given_names": self.given_names,
            "nationality": self.nationality,
            "personal_number": self.personal_number,
            "mrz_type": self.mrz_type,
        }


class MRZParser:
    """Parses MRZ strings according to ICAO Doc 9303."""

    @staticmethod
    def parse_td3(lines: list[str]) -> MRZData:
        """Parse TD3 (e-passport) MRZ format (2 lines, 44 chars each)."""
        if len(lines) != 2:
            raise MRZError(f"TD3 requires 2 lines, got {len(lines)}")

        line1 = lines[0].upper()
        line2 = lines[1].upper()

        if len(line1) != 44 or len(line2) != 44:
            raise MRZError("TD3 lines must be 44 characters each")

        # Parse line 1: P<USA<SURNAME<<GIVEN<NAMES<<<<<<<<<<<<<<<<<<<
        document_type = line1[0]
        issuing_state = line1[2:5]

        # Parse name
        name_parts = line1[5:].split("<<")
        surname = name_parts[0].replace("<", " ").strip()
        given_names = name_parts[1].replace("<", " ").strip() if len(name_parts) > 1 else ""

        # Parse line 2: A12345678<USA8001018M2501019<<<<<<<<<<<<<<04
        document_number = line2[0:9].replace("<", "")
        nationality = line2[10:13]
        birth_date_str = line2[13:19]
        sex = line2[20]
        expiry_date_str = line2[21:27]
        personal_number = line2[28:42].replace("<", "")

        # Format dates
        birth_date = MRZParser._format_date(birth_date_str)
        expiry_date = MRZParser._format_date(expiry_date_str)

        logger.info("TD3 MRZ parsed", document_number=document_number, issuing_state=issuing_state)

        return MRZData(
            document_type=document_type,
            issuing_state=issuing_state,
            document_number=document_number,
            birth_date=birth_date,
            expiry_date=expiry_date,
            sex=sex,
            surname=surname,
            given_names=given_names,
            nationality=nationality,
            personal_number=personal_number,
            mrz_type="TD3",
        )

    @staticmethod
    def parse_td1(lines: list[str]) -> MRZData:
        """Parse TD1 (ID card) MRZ format (3 lines, 30 chars each)."""
        if len(lines) != 3:
            raise MRZError(f"TD1 requires 3 lines, got {len(lines)}")

        line1 = lines[0].upper()
        line2 = lines[1].upper()
        line3 = lines[2].upper()

        if len(line1) != 30 or len(line2) != 30 or len(line3) != 30:
            raise MRZError("TD1 lines must be 30 characters each")

        # Parse line 1: I<UTO<ERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<
        document_type = line1[0]
        issuing_state = line1[2:5]

        # Parse name
        name_parts = line1[5:].split("<<")
        surname = name_parts[0].replace("<", " ").strip()
        given_names = name_parts[1].replace("<", " ").strip() if len(name_parts) > 1 else ""

        # Parse line 2: A12345678<UTO8001018F2501019<<<<<<<<<<<<<
        document_number = line2[0:9].replace("<", "")
        nationality = line2[10:13]
        birth_date_str = line2[13:19]
        sex = line2[20]
        expiry_date_str = line2[21:27]

        # Parse line 3 for optional personal number
        personal_number = line3[0:15].replace("<", "")

        # Format dates
        birth_date = MRZParser._format_date(birth_date_str)
        expiry_date = MRZParser._format_date(expiry_date_str)

        logger.info("TD1 MRZ parsed", document_number=document_number, issuing_state=issuing_state)

        return MRZData(
            document_type=document_type,
            issuing_state=issuing_state,
            document_number=document_number,
            birth_date=birth_date,
            expiry_date=expiry_date,
            sex=sex,
            surname=surname,
            given_names=given_names,
            nationality=nationality,
            personal_number=personal_number,
            mrz_type="TD1",
        )

    @staticmethod
    def parse_td2(lines: list[str]) -> MRZData:
        """Parse TD2 (legacy passport) MRZ format (2 lines, 36 chars each)."""
        if len(lines) != 2:
            raise MRZError(f"TD2 requires 2 lines, got {len(lines)}")

        line1 = lines[0].upper()
        line2 = lines[1].upper()

        if len(line1) != 36 or len(line2) != 36:
            raise MRZError("TD2 lines must be 36 characters each")

        # Parse line 1: I<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<
        document_type = line1[0]
        issuing_state = line1[2:5]

        # Parse name (combined in TD2)
        name_field = line1[5:]
        name_parts = name_field.split("<<")
        surname = name_parts[0].replace("<", " ").strip()
        given_names = name_parts[1].replace("<", " ").strip() if len(name_parts) > 1 else ""

        # Parse line 2: A123456785UTO8001018F2501019<<<<<<<<<<<<<
        document_number = line2[0:9].replace("<", "")
        nationality = line2[10:13]
        birth_date_str = line2[13:19]
        sex = line2[20]
        expiry_date_str = line2[21:27]

        # Format dates
        birth_date = MRZParser._format_date(birth_date_str)
        expiry_date = MRZParser._format_date(expiry_date_str)

        logger.info("TD2 MRZ parsed", document_number=document_number, issuing_state=issuing_state)

        return MRZData(
            document_type=document_type,
            issuing_state=issuing_state,
            document_number=document_number,
            birth_date=birth_date,
            expiry_date=expiry_date,
            sex=sex,
            surname=surname,
            given_names=given_names,
            nationality=nationality,
            mrz_type="TD2",
        )

    @staticmethod
    def _format_date(date_str: str) -> str:
        """Format MRZ date (YYMMDD) to ISO format (YYYY-MM-DD)."""
        if len(date_str) != 6:
            return date_str

        year = int(date_str[0:2])
        month = date_str[2:4]
        day = date_str[4:6]

        # Determine century (assuming valid passports are not from 1900-1999 if year > 50)
        # This is a simplified heuristic
        full_year = 2000 + year if year < 50 else 1900 + year

        return f"{full_year:04d}-{month}-{day}"

    @staticmethod
    def auto_parse(mrz_text: str) -> MRZData:
        """Automatically detect and parse MRZ format."""
        lines = [line.strip() for line in mrz_text.split("\n") if line.strip()]

        if len(lines) == 2:
            line_length = len(lines[0])
            if line_length == 44:
                return MRZParser.parse_td3(lines)
            elif line_length == 36:
                return MRZParser.parse_td2(lines)
        elif len(lines) == 3 and len(lines[0]) == 30:
            return MRZParser.parse_td1(lines)

        raise MRZError(f"Unable to auto-detect MRZ format: {len(lines)} lines, length {len(lines[0]) if lines else 0}")

    @staticmethod
    def validate_check_digits(mrz_data: MRZData, lines: list[str]) -> dict[str, Any]:
        """Validate check digits for parsed MRZ."""
        if mrz_data.mrz_type == "TD3":
            line1_valid = MRZCheckDigitValidator.validate_td3_line1(lines[0])
            line2_valid = MRZCheckDigitValidator.validate_td3_line2(lines[1])
            return {
                "valid": line1_valid["valid"] and line2_valid["valid"],
                "line1": line1_valid,
                "line2": line2_valid,
            }
        elif mrz_data.mrz_type == "TD1":
            return MRZCheckDigitValidator.validate_td1(lines)
        elif mrz_data.mrz_type == "TD2":
            # TD2 has similar validation to TD3 but with 36-char lines
            # Simplified for now
            return {"valid": True, "note": "TD2 check digit validation not fully implemented"}
        else:
            return {"valid": False, "reason": "Unknown MRZ type"}
