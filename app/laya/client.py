"""Laya System 1 decision engine integration for passport expiry classification.

Laya is a local fast non-autoregressive decision model. It accepts a text
"state" (context) and a set of structured questions, then returns calibrated
probability answers.

Usage:
    classifier = LayaClassifier(checkpoint_path)
    result = classifier.classify(extraction_result)
    # result = {"expired": True/False/None, "confidence": 0.92}
"""

from datetime import date
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class LayaClassifier:
    """Passport expiry classifier using the Laya System 1 decision engine."""

    def __init__(self, checkpoint_path: str) -> None:
        import laya

        logger.info("Loading Laya model checkpoint", checkpoint=checkpoint_path)
        self._agent = laya.load(checkpoint_path)
        logger.info("Laya model loaded")

    def classify(self, extraction_result: dict[str, Any]) -> dict[str, Any]:
        """Classify whether the passport is expired using Laya.

        Builds a text context from the extracted passport data and asks
        Laya: "Is this passport expired as of today?"

        Args:
            extraction_result: Dict returned by ExtractionService.extract_from_image()

        Returns:
            {"expired": bool | None, "confidence": float}
        """
        import laya

        state = _build_state(extraction_result)
        logger.info("Sending state to Laya model", state_length=len(state))

        questions = {
            "expired": {
                "type": "noul",
                "instructions": (
                    "Based on the passport data above and today's date, "
                    "is the passport expired?"
                ),
            }
        }

        result = laya.decide(self._agent, state, questions=questions, return_details=True)

        expired_answer = result.answers.get("expired") or {}
        # noul type: probability that the answer is True
        noul_prob = float(expired_answer.get("noul", 0.5))
        expired = noul_prob >= 0.5
        confidence = result.answer_confidence.get("expired") or abs(noul_prob - 0.5) * 2

        logger.info("Laya classified passport", expired=expired, confidence=confidence)
        return {"expired": expired, "confidence": float(confidence)}


def _build_state(extraction_result: dict[str, Any]) -> str:
    """Format extracted passport data as a text context for Laya."""
    lines = [f"Today's date: {date.today().isoformat()}"]

    mrz_data = extraction_result.get("mrz_data") or {}

    expiry = mrz_data.get("expiry_date_normalized") or mrz_data.get("expiry_date")
    if expiry:
        lines.append(f"Passport expiry date: {expiry}")

    birth = mrz_data.get("birth_date_normalized") or mrz_data.get("birth_date")
    if birth:
        lines.append(f"Date of birth: {birth}")

    doc_num = mrz_data.get("document_number")
    if doc_num:
        lines.append(f"Document number: {doc_num}")

    nationality = mrz_data.get("nationality")
    if nationality:
        lines.append(f"Nationality: {nationality}")

    issuer = mrz_data.get("issuing_state")
    if issuer:
        lines.append(f"Issuing state: {issuer}")

    mrz_type = mrz_data.get("mrz_type")
    if mrz_type:
        lines.append(f"MRZ type: {mrz_type}")

    if not mrz_data:
        lines.append("MRZ data: not detected")

    ocr_fields = extraction_result.get("ocr_fields") or {}
    if ocr_fields:
        lines.append("Additional OCR fields: " + ", ".join(
            f"{k}={v}" for k, v in ocr_fields.items() if v
        ))

    return "\n".join(lines)
