"""Decision schemas."""

from typing import Any

from pydantic import BaseModel


class DecisionResponse(BaseModel):
    """Decision response."""

    decision_id: str
    outcome: str
    confidence: float
    reasoning: str
    policy_version: str | None = None
    triggered_rules: list[str] = []
    validation_summary: dict[str, Any] = {}
