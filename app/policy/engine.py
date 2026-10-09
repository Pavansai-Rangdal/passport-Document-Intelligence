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

    def evaluate(
        self,
        validation_results: list[dict],
        system_one_recommendation: str | None = None,
        system_one_confidence: float | None = None,
    ) -> dict[str, Any]:
        """
        Evaluate policy and return decision.

        Args:
            validation_results: List of validation result dictionaries
            system_one_recommendation: Optional recommendation from System One
            system_one_confidence: Optional confidence score from System One

        Returns:
            dict: Decision outcome with reasoning
        """
        logger.info(
            "Evaluating policy",
            version=self.current_version.version,
            validation_count=len(validation_results),
            system_one_available=system_one_recommendation is not None,
        )

        outcome, reasoning, triggered_rules = self.rules.evaluate(
            validation_results=validation_results,
            system_one_recommendation=system_one_recommendation,
            system_one_confidence=system_one_confidence,
        )

        result = {
            "outcome": outcome.value,
            "policy_version": self.current_version.version,
            "reasoning": reasoning,
            "triggered_rules": triggered_rules,
            "system_one_recommendation": system_one_recommendation,
            "system_one_confidence": system_one_confidence,
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
