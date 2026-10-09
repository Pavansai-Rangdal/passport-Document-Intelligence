"""Validation result data structures."""

from dataclasses import dataclass
from typing import Any

from app.db.models import RuleCategory, ValidationSeverity


@dataclass
class ValidationResult:
    """Result of a validation rule check."""

    rule_name: str
    rule_category: RuleCategory
    severity: ValidationSeverity
    passed: bool
    message: str
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_name": self.rule_name,
            "rule_category": self.rule_category.value,
            "severity": self.severity.value,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
        }
