"""Date validation rules."""

from datetime import datetime

from app.core.logging import get_logger
from app.db.models import RuleCategory, ValidationSeverity
from app.extraction.normalization import DateNormalizer
from app.validation.result import ValidationResult

logger = get_logger(__name__)


class DateRules:
    """Date validation rules."""

    @staticmethod
    def validate_not_expired(expiry_date: str) -> ValidationResult:
        """Check if passport is not expired."""
        if not expiry_date:
            return ValidationResult(
                rule_name="passport_not_expired",
                rule_category=RuleCategory.EXPIRY,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message="Expiry date is required",
            )

        try:
            expiry = datetime.fromisoformat(expiry_date)
            if expiry < datetime.utcnow():
                return ValidationResult(
                    rule_name="passport_not_expired",
                    rule_category=RuleCategory.EXPIRY,
                    severity=ValidationSeverity.ERROR,
                    passed=False,
                    message=f"Passport expired on {expiry_date}",
                    details={"expiry_date": expiry_date},
                )

            return ValidationResult(
                rule_name="passport_not_expired",
                rule_category=RuleCategory.EXPIRY,
                severity=ValidationSeverity.INFO,
                passed=True,
                message="Passport is not expired",
            )
        except ValueError:
            return ValidationResult(
                rule_name="passport_not_expired",
                rule_category=RuleCategory.EXPIRY,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message=f"Invalid expiry date format: {expiry_date}",
            )

    @staticmethod
    def validate_reasonable_birth_date(birth_date: str) -> ValidationResult:
        """Check if birth date is reasonable."""
        if not birth_date:
            return ValidationResult(
                rule_name="reasonable_birth_date",
                rule_category=RuleCategory.EXPIRY,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message="Birth date is required",
            )

        if not DateNormalizer.is_reasonable_birth_date(birth_date):
            return ValidationResult(
                rule_name="reasonable_birth_date",
                rule_category=RuleCategory.EXPIRY,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message=f"Birth date is not reasonable: {birth_date}",
                details={"birth_date": birth_date},
            )

        return ValidationResult(
            rule_name="reasonable_birth_date",
            rule_category=RuleCategory.EXPIRY,
            severity=ValidationSeverity.INFO,
            passed=True,
            message="Birth date is reasonable",
        )

    @staticmethod
    def validate_issue_before_expiry(issue_date: str, expiry_date: str) -> ValidationResult:
        """Check that issue date is before expiry date."""
        if not issue_date or not expiry_date:
            return ValidationResult(
                rule_name="issue_before_expiry",
                rule_category=RuleCategory.EXPIRY,
                severity=ValidationSeverity.WARNING,
                passed=False,
                message="Issue date and expiry date are required",
            )

        try:
            issue = datetime.fromisoformat(issue_date)
            expiry = datetime.fromisoformat(expiry_date)

            if issue >= expiry:
                return ValidationResult(
                    rule_name="issue_before_expiry",
                    rule_category=RuleCategory.EXPIRY,
                    severity=ValidationSeverity.ERROR,
                    passed=False,
                    message=f"Issue date ({issue_date}) must be before expiry date ({expiry_date})",
                )

            return ValidationResult(
                rule_name="issue_before_expiry",
                rule_category=RuleCategory.EXPIRY,
                severity=ValidationSeverity.INFO,
                passed=True,
                message="Issue date is before expiry date",
            )
        except ValueError:
            return ValidationResult(
                rule_name="issue_before_expiry",
                rule_category=RuleCategory.EXPIRY,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message="Invalid date format",
            )
