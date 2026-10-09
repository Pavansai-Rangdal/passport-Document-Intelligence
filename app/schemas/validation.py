"""Validation schemas."""

from typing import Any

from pydantic import BaseModel


class ValidationResultResponse(BaseModel):
    """Validation result response."""

    rule_name: str
    rule_category: str
    severity: str
    passed: bool
    message: str
    details: dict[str, Any] | None = None


class ValidationSummaryResponse(BaseModel):
    """Validation summary response."""

    total: int
    passed: int
    failed: int
    errors: int
    warnings: int
    overall_passed: bool
