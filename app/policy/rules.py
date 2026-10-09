"""Deterministic policy rules for decision making."""

from app.core.logging import get_logger
from app.db.models import DecisionOutcome

logger = get_logger(__name__)


class PolicyRules:
    """Deterministic policy rules for final decision making."""

    @staticmethod
    def evaluate(
        validation_results: list[dict],
        system_one_recommendation: str | None = None,
        system_one_confidence: float | None = None,
    ) -> tuple[DecisionOutcome, str, list[str]]:
        """
        Evaluate policy rules and return final decision.

        Returns:
            tuple: (outcome, reasoning, triggered_rules)
        """
        triggered_rules = []
        reasoning_parts = []

        # Rule 1: Critical validation errors always result in FAIL_RULE
        critical_errors = [
            r["rule_name"]
            for r in validation_results
            if not r["passed"] and r["severity"] == "error"
        ]

        if critical_errors:
            triggered_rules.extend(critical_errors)
            reasoning_parts.append(f"Critical validation errors: {', '.join(critical_errors)}")
            return (
                DecisionOutcome.FAIL_RULE,
                "Document failed critical validation rules",
                triggered_rules,
            )

        # Rule 2: If System One is available and recommends fail with high confidence, fail
        if system_one_recommendation and system_one_confidence is not None:
            if system_one_recommendation.lower() == "fail" and system_one_confidence > 0.8:
                triggered_rules.append("system_one_high_confidence_fail")
                reasoning_parts.append(
                    f"System One recommends fail with high confidence ({system_one_confidence:.2f})"
                )
                return (
                    DecisionOutcome.FAIL_RULE,
                    "System One recommends rejection with high confidence",
                    triggered_rules,
                )

        # Rule 3: If System One recommends review or has low confidence, review required
        if system_one_recommendation:
            if system_one_recommendation.lower() == "review":
                triggered_rules.append("system_one_review_recommendation")
                reasoning_parts.append("System One recommends manual review")
                return (
                    DecisionOutcome.REVIEW_REQUIRED,
                    "System One recommends manual review",
                    triggered_rules,
                )
            elif system_one_confidence is not None and system_one_confidence < 0.7:
                triggered_rules.append("system_one_low_confidence")
                reasoning_parts.append(
                    f"System One has low confidence ({system_one_confidence:.2f})"
                )
                return (
                    DecisionOutcome.REVIEW_REQUIRED,
                    "System One confidence below threshold",
                    triggered_rules,
                )

        # Rule 4: Warnings trigger review
        warnings = [
            r["rule_name"]
            for r in validation_results
            if not r["passed"] and r["severity"] == "warning"
        ]

        if warnings:
            triggered_rules.extend(warnings)
            reasoning_parts.append(f"Validation warnings: {', '.join(warnings)}")
            return (
                DecisionOutcome.REVIEW_REQUIRED,
                "Document has validation warnings requiring review",
                triggered_rules,
            )

        # Rule 5: Insufficient data if missing critical fields
        mrz_present = any(r["rule_name"] == "mrz_present" and r["passed"] for r in validation_results)
        if not mrz_present:
            triggered_rules.append("insufficient_mrz_data")
            reasoning_parts.append("MRZ data not present or incomplete")
            return (
                DecisionOutcome.INSUFFICIENT_DATA,
                "Insufficient data for verification",
                triggered_rules,
            )

        # Rule 6: All validations passed and System One agrees (if available) -> PASS
        if system_one_recommendation:
            if system_one_recommendation.lower() == "pass":
                triggered_rules.append("system_one_pass_recommendation")
                reasoning_parts.append("System One recommends pass")
            else:
                # System One available but didn't recommend pass - default to review
                triggered_rules.append("system_one_ambiguous")
                reasoning_parts.append("System One recommendation ambiguous")
                return (
                    DecisionOutcome.REVIEW_REQUIRED,
                    "System One recommendation requires review",
                    triggered_rules,
                )

        # Default: All validations passed without System One or with pass recommendation
        reasoning_parts.append("All validations passed")
        return (
            DecisionOutcome.PASS_SCREENING,
            "Document passed all validation rules",
            triggered_rules,
        )
