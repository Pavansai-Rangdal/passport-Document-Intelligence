"""Schema validation rules for passport fields."""


import re

from app.core.logging import get_logger
from app.db.models import RuleCategory, ValidationSeverity
from app.validation.result import ValidationResult

logger = get_logger(__name__)


class SchemaRules:
    """Schema validation rules for passport data."""

    @staticmethod
    def validate_document_number(value: str) -> ValidationResult:
        """Validate document number format."""
        if not value:
            return ValidationResult(
                rule_name="document_number_format",
                rule_category=RuleCategory.SCHEMA,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message="Document number is required",
            )

        # Document number: 1-2 letters followed by 6-9 digits
        pattern = r"^[A-Z]{1,2}\d{6,9}$"
        if not re.match(pattern, value.replace("<", "")):
            return ValidationResult(
                rule_name="document_number_format",
                rule_category=RuleCategory.SCHEMA,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message=f"Document number format invalid: {value}",
                details={"expected": "1-2 letters + 6-9 digits", "actual": value},
            )

        return ValidationResult(
            rule_name="document_number_format",
            rule_category=RuleCategory.SCHEMA,
            severity=ValidationSeverity.INFO,
            passed=True,
            message="Document number format valid",
        )

    @staticmethod
    def validate_country_code(value: str) -> ValidationResult:
        """Validate 3-letter country code."""
        if not value:
            return ValidationResult(
                rule_name="country_code_format",
                rule_category=RuleCategory.SCHEMA,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message="Country code is required",
            )

        if len(value) != 3 or not value.isalpha():
            return ValidationResult(
                rule_name="country_code_format",
                rule_category=RuleCategory.SCHEMA,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message=f"Country code must be 3 letters: {value}",
            )

        return ValidationResult(
            rule_name="country_code_format",
            rule_category=RuleCategory.SCHEMA,
            severity=ValidationSeverity.INFO,
            passed=True,
            message="Country code format valid",
        )

    @staticmethod
    def validate_sex(value: str) -> ValidationResult:
        """Validate sex field."""
        if not value:
            return ValidationResult(
                rule_name="sex_format",
                rule_category=RuleCategory.SCHEMA,
                severity=ValidationSeverity.WARNING,
                passed=False,
                message="Sex field is missing",
            )

        if value.upper() not in ("M", "F", "X"):
            return ValidationResult(
                rule_name="sex_format",
                rule_category=RuleCategory.SCHEMA,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message=f"Sex must be M, F, or X: {value}",
            )

        return ValidationResult(
            rule_name="sex_format",
            rule_category=RuleCategory.SCHEMA,
            severity=ValidationSeverity.INFO,
            passed=True,
            message="Sex field valid",
        )

    @staticmethod
    def validate_date_format(value: str, field_name: str) -> ValidationResult:
        """Validate ISO date format."""
        if not value:
            return ValidationResult(
                rule_name=f"{field_name}_format",
                rule_category=RuleCategory.SCHEMA,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message=f"{field_name} is required",
            )

        # Check ISO format (YYYY-MM-DD)
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(pattern, value):
            return ValidationResult(
                rule_name=f"{field_name}_format",
                rule_category=RuleCategory.SCHEMA,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message=f"{field_name} must be in ISO format (YYYY-MM-DD): {value}",
            )

        return ValidationResult(
            rule_name=f"{field_name}_format",
            rule_category=RuleCategory.SCHEMA,
            severity=ValidationSeverity.INFO,
            passed=True,
            message=f"{field_name} format valid",
        )
