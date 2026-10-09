"""Evidence schemas."""

from typing import Any

from pydantic import BaseModel


class EvidenceResponse(BaseModel):
    """Evidence response."""

    evidence_type: str
    source: str
    data: dict[str, Any]
    confidence: float | None = None
    timestamp: str | None = None
