"""MRZ validation rules."""

from app.core.logging import get_logger
from app.db.models import RuleCategory, ValidationSeverity
from app.extraction.mrz import MRZParser
from app.validation.result import ValidationResult

logger = get_logger(__name__)


class MRZRules:
    """MRZ validation rules."""

    @staticmethod
    def validate_check_digits(mrz_text: str) -> ValidationResult:
        """Validate MRZ check digits."""
        try:
            lines = [line.strip() for line in mrz_text.split("\n") if line.strip()]
            mrz_data = MRZParser.auto_parse(mrz_text)
            validation = MRZParser.validate_check_digits(mrz_data, lines)

            if not validation.get("valid"):
                return ValidationResult(
                    rule_name="mrz_check_digits",
                    rule_category=RuleCategory.MRZ_CHECKSUM,
                    severity=ValidationSeverity.ERROR,
                    passed=False,
                    message="MRZ check digit validation failed",
                    details=validation,
                )

            return ValidationResult(
                rule_name="mrz_check_digits",
                rule_category=RuleCategory.MRZ_CHECKSUM,
                severity=ValidationSeverity.INFO,
                passed=True,
                message="MRZ check digits valid",
                details=validation,
            )
        except Exception as e:
            return ValidationResult(
                rule_name="mrz_check_digits",
                rule_category=RuleCategory.MRZ_CHECKSUM,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message=f"MRZ check digit validation error: {e}",
            )

    @staticmethod
    def validate_mrz_present(mrz_data: dict | None) -> ValidationResult:
        """Validate that MRZ data was extracted."""
        if not mrz_data:
            return ValidationResult(
                rule_name="mrz_present",
                rule_category=RuleCategory.MRZ_CHECKSUM,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message="MRZ data not extracted",
            )

        required_fields = ["document_number", "issuing_state", "birth_date", "expiry_date"]
        missing = [f for f in required_fields if not mrz_data.get(f)]

        if missing:
            return ValidationResult(
                rule_name="mrz_present",
                rule_category=RuleCategory.MRZ_CHECKSUM,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message=f"MRZ missing required fields: {missing}",
                details={"missing_fields": missing},
            )

        return ValidationResult(
            rule_name="mrz_present",
            rule_category=RuleCategory.MRZ_CHECKSUM,
            severity=ValidationSeverity.INFO,
            passed=True,
            message="MRZ data complete",
        )
