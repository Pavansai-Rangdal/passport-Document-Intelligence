"""Validation rule registry."""

from collections.abc import Callable
from typing import Any

from app.validation.consistency_rules import ConsistencyRules
from app.validation.date_rules import DateRules
from app.validation.image_rules import ImageRules
from app.validation.mrz_rules import MRZRules
from app.validation.result import ValidationResult
from app.validation.schema_rules import SchemaRules


class ValidationRuleRegistry:
    """Registry for validation rules."""

    def __init__(self) -> None:
        self._rules: dict[str, Callable[..., ValidationResult]] = {}
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        """Register default validation rules."""
        schema = SchemaRules()
        date = DateRules()
        image = ImageRules()
        mrz = MRZRules()
        consistency = ConsistencyRules()

        # Schema rules
        self.register("document_number_format", schema.validate_document_number)
        self.register("country_code_format", schema.validate_country_code)
        self.register("sex_format", schema.validate_sex)

        # Date rules
        self.register("passport_not_expired", date.validate_not_expired)
        self.register("reasonable_birth_date", date.validate_reasonable_birth_date)
        self.register("issue_before_expiry", date.validate_issue_before_expiry)

        # Image rules
        self.register("image_dimensions", image.validate_dimensions)
        self.register("image_blur", image.validate_blur_score)
        self.register("image_brightness", image.validate_brightness)
        self.register("mrz_detected", image.validate_mrz_detected)

        # MRZ rules
        self.register("mrz_check_digits", mrz.validate_check_digits)
        self.register("mrz_present", mrz.validate_mrz_present)

        # Consistency rules
        self.register("nationality_issuing_state_match", consistency.validate_nationality_issuing_state_match)
        self.register("viz_mrz_document_number_match", consistency.validate_viz_mrz_consistency)
        self.register("birth_date_before_expiry", consistency.validate_birth_date_before_expiry)

    def register(self, name: str, rule_func: Callable[..., ValidationResult]) -> None:
        """Register a validation rule."""
        self._rules[name] = rule_func

    def get_rule(self, name: str) -> Callable[..., ValidationResult] | None:
        """Get a registered rule by name."""
        return self._rules.get(name)

    def list_rules(self) -> list[str]:
        """List all registered rule names."""
        return list(self._rules.keys())

    def execute_rule(self, name: str, *args: Any, **kwargs: Any) -> ValidationResult:
        """Execute a registered rule."""
        rule = self.get_rule(name)
        if not rule:
            raise ValueError(f"Rule not registered: {name}")
        return rule(*args, **kwargs)
