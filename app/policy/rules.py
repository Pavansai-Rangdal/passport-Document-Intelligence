"""Deterministic policy rules for decision making."""

from app.core.logging import get_logger
from app.db.models import DecisionOutcome

logger = get_logger(__name__)


class PolicyRules:
    """Deterministic policy rules for final decision making."""

    @staticmethod
    def evaluate(
        validation_results: list[dict],
    ) -> tuple[DecisionOutcome, str, list[str]]:
        """
        Evaluate policy rules and return final decision.

        Returns:
            tuple: (outcome, reasoning, triggered_rules)
        """
        triggered_rules = []

        # Rule 1: Critical validation errors always result in FAIL_RULE
        critical_errors = [
            r["rule_name"]
            for r in validation_results
            if not r["passed"] and r["severity"] == "error"
        ]

        if critical_errors:
            triggered_rules.extend(critical_errors)
            return (
                DecisionOutcome.FAIL_RULE,
                f"Document failed critical validation rules: {', '.join(critical_errors)}",
                triggered_rules,
            )

        # Rule 2: Warnings trigger review
        warnings = [
            r["rule_name"]
            for r in validation_results
            if not r["passed"] and r["severity"] == "warning"
        ]

        if warnings:
            triggered_rules.extend(warnings)
            return (
                DecisionOutcome.REVIEW_REQUIRED,
                f"Document has validation warnings: {', '.join(warnings)}",
                triggered_rules,
            )

        # Rule 3: Insufficient data if MRZ missing
        mrz_present = any(r["rule_name"] == "mrz_present" and r["passed"] for r in validation_results)
        if not mrz_present:
            triggered_rules.append("insufficient_mrz_data")
            return (
                DecisionOutcome.INSUFFICIENT_DATA,
                "Insufficient data for verification",
                triggered_rules,
            )

        # Rule 4: All validations passed
        return (
            DecisionOutcome.PASS_SCREENING,
            "Document passed all validation rules",
            triggered_rules,
        )
