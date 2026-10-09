"""Cross-field consistency validation rules."""

from app.core.logging import get_logger
from app.db.models import RuleCategory, ValidationSeverity
from app.validation.result import ValidationResult

logger = get_logger(__name__)


class ConsistencyRules:
    """Cross-field consistency validation rules."""

    @staticmethod
    def validate_nationality_issuing_state_match(
        nationality: str | None,
        issuing_state: str | None,
    ) -> ValidationResult:
        """Validate that nationality matches issuing state (warning if different)."""
        if not nationality or not issuing_state:
            return ValidationResult(
                rule_name="nationality_issuing_state_match",
                rule_category=RuleCategory.CROSS_FIELD,
                severity=ValidationSeverity.INFO,
                passed=True,
                message="Cannot verify nationality/issuing state match (fields missing)",
            )

        if nationality.upper() != issuing_state.upper():
            return ValidationResult(
                rule_name="nationality_issuing_state_match",
                rule_category=RuleCategory.CROSS_FIELD,
                severity=ValidationSeverity.WARNING,
                passed=False,
                message=f"Nationality ({nationality}) differs from issuing state ({issuing_state})",
                details={"nationality": nationality, "issuing_state": issuing_state},
            )

        return ValidationResult(
            rule_name="nationality_issuing_state_match",
            rule_category=RuleCategory.CROSS_FIELD,
            severity=ValidationSeverity.INFO,
            passed=True,
            message="Nationality matches issuing state",
        )

    @staticmethod
    def validate_viz_mrz_consistency(
        viz_document_number: str | None,
        mrz_document_number: str | None,
    ) -> ValidationResult:
        """Validate that VIZ and MRZ document numbers match."""
        if not viz_document_number or not mrz_document_number:
            return ValidationResult(
                rule_name="viz_mrz_document_number_match",
                rule_category=RuleCategory.CROSS_FIELD,
                severity=ValidationSeverity.INFO,
                passed=True,
                message="Cannot verify VIZ/MRZ document number match (fields missing)",
            )

        # Normalize for comparison
        viz_normalized = viz_document_number.upper().replace("<", "").replace(" ", "")
        mrz_normalized = mrz_document_number.upper().replace("<", "").replace(" ", "")

        if viz_normalized != mrz_normalized:
            return ValidationResult(
                rule_name="viz_mrz_document_number_match",
                rule_category=RuleCategory.CROSS_FIELD,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message=f"VIZ document number ({viz_document_number}) does not match MRZ ({mrz_document_number})",
                details={"viz": viz_document_number, "mrz": mrz_document_number},
            )

        return ValidationResult(
            rule_name="viz_mrz_document_number_match",
            rule_category=RuleCategory.CROSS_FIELD,
            severity=ValidationSeverity.INFO,
            passed=True,
            message="VIZ and MRZ document numbers match",
        )

    @staticmethod
    def validate_birth_date_before_expiry(
        birth_date: str | None,
        expiry_date: str | None,
    ) -> ValidationResult:
        """Validate that birth date is before expiry date."""
        if not birth_date or not expiry_date:
            return ValidationResult(
                rule_name="birth_date_before_expiry",
                rule_category=RuleCategory.CROSS_FIELD,
                severity=ValidationSeverity.INFO,
                passed=True,
                message="Cannot verify birth/expiry date order (fields missing)",
            )

        try:
            from datetime import datetime

            birth = datetime.fromisoformat(birth_date)
            expiry = datetime.fromisoformat(expiry_date)

            if birth >= expiry:
                return ValidationResult(
                    rule_name="birth_date_before_expiry",
                    rule_category=RuleCategory.CROSS_FIELD,
                    severity=ValidationSeverity.ERROR,
                    passed=False,
                    message=f"Birth date ({birth_date}) must be before expiry date ({expiry_date})",
                )

            return ValidationResult(
                rule_name="birth_date_before_expiry",
                rule_category=RuleCategory.CROSS_FIELD,
                severity=ValidationSeverity.INFO,
                passed=True,
                message="Birth date is before expiry date",
            )
        except ValueError:
            return ValidationResult(
                rule_name="birth_date_before_expiry",
                rule_category=RuleCategory.CROSS_FIELD,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message="Invalid date format",
            )
