"""Classification response schema."""

from typing import Optional

from pydantic import BaseModel


class ClassificationResponse(BaseModel):
    expired: Optional[bool]
    expiry_date: Optional[str]
    confidence: float
    mrz_detected: bool
    method: str
    message: str
