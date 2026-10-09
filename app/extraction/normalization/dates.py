"""Date normalization utilities."""

from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class DateNormalizer:
    """Normalizes dates to ISO format."""

    DATE_FORMATS = [
        "%Y-%m-%d",  # ISO
        "%d/%m/%Y",  # DD/MM/YYYY
        "%d.%m.%Y",  # DD.MM.YYYY
        "%m/%d/%Y",  # MM/DD/YYYY
        "%Y/%m/%d",  # YYYY/MM/DD
        "%d %b %Y",  # DD Mon YYYY
        "%d %B %Y",  # DD Month YYYY
        "%Y%m%d",  # YYMMDD (MRZ format)
        "%y%m%d",  # YYMMDD (MRZ 2-digit year)
    ]

    @staticmethod
    def normalize(date_str: str) -> str | None:
        """Normalize date string to ISO format (YYYY-MM-DD)."""
        if not date_str:
            return None

        date_str = date_str.strip()

        # Handle MRZ format (YYMMDD)
        if len(date_str) == 6 and date_str.isdigit():
            year = int(date_str[0:2])
            month = date_str[2:4]
            day = date_str[4:6]

            # Determine century
            full_year = 2000 + year if year < 50 else 1900 + year
            return f"{full_year:04d}-{month}-{day}"

        # Try various formats
        for fmt in DateNormalizer.DATE_FORMATS:
            try:
                parsed = datetime.strptime(date_str, fmt)
                # Handle 2-digit years
                if parsed.year < 100:
                    parsed = parsed.replace(year=parsed.year + 2000 if parsed.year < 50 else parsed.year + 1900)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

        logger.warning("Failed to normalize date", date_str=date_str)
        return None

    @staticmethod
    def is_valid_iso_date(date_str: str) -> bool:
        """Check if string is a valid ISO date."""
        try:
            datetime.fromisoformat(date_str)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_expired(expiry_date: str) -> bool:
        """Check if date is in the past."""
        try:
            expiry = datetime.fromisoformat(expiry_date)
            return expiry < datetime.utcnow()
        except ValueError:
            return False

    @staticmethod
    def is_reasonable_birth_date(birth_date: str) -> bool:
        """Check if birth date is reasonable (not in future, not too old)."""
        try:
            birth = datetime.fromisoformat(birth_date)
            now = datetime.utcnow()
            age_years = (now - birth).days / 365.25

            # Reasonable age range: 0-120 years
            return 0 <= age_years <= 120
        except ValueError:
            return False
