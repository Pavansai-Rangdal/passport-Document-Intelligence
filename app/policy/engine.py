"""Policy engine for deterministic decision making."""

from typing import Any

from app.core.logging import get_logger
from app.policy.rules import PolicyRules
from app.policy.versions import PolicyVersions

logger = get_logger(__name__)


class PolicyEngine:
    """Deterministic policy engine for final decision making."""

    def __init__(self) -> None:
        self.rules = PolicyRules()
        self.current_version = PolicyVersions.get_current()

    def evaluate(self, validation_results: list[dict]) -> dict[str, Any]:
        """
        Evaluate policy and return decision.

        Args:
            validation_results: List of validation result dictionaries

        Returns:
            dict: Decision outcome with reasoning
        """
        logger.info(
            "Evaluating policy",
            version=self.current_version.version,
            validation_count=len(validation_results),
        )

        outcome, reasoning, triggered_rules = self.rules.evaluate(
            validation_results=validation_results,
        )

        result = {
            "outcome": outcome.value,
            "policy_version": self.current_version.version,
            "reasoning": reasoning,
            "triggered_rules": triggered_rules,
        }

        logger.info(
            "Policy evaluation completed",
            outcome=outcome.value,
            triggered_rules=len(triggered_rules),
        )

        return result

    def get_policy_info(self) -> dict[str, Any]:
        """Get information about current policy."""
        return {
            "version": self.current_version.version,
            "description": self.current_version.description,
            "rules": self.current_version.rules,
        }
