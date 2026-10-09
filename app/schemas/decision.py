"""Decision schemas."""

from typing import Any

from pydantic import BaseModel


class DecisionResponse(BaseModel):
    """Decision response."""

    decision_id: str
    outcome: str
    confidence: float
    reasoning: str
    system_one_recommendation: str | None = None
    system_one_confidence: float | None = None
    policy_version: str | None = None
    triggered_rules: list[str] = []
    validation_summary: dict[str, Any] = {}
