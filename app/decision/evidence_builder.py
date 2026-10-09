"""Evidence builder for decision making."""

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class EvidenceBuilder:
    """Builds evidence payloads for decision making."""

    @staticmethod
    def build_extraction_evidence(extraction_data: dict[str, Any]) -> dict[str, Any]:
        """Build evidence from extraction data."""
        return {
            "mrz_detected": extraction_data.get("mrz_detected", False),
            "mrz_data": extraction_data.get("mrz_data"),
            "ocr_fields": extraction_data.get("ocr_fields"),
            "normalized_fields": extraction_data.get("normalized_fields"),
            "quality": extraction_data.get("quality"),
            "ocr_engine_used": extraction_data.get("ocr_engine_used"),
        }

    @staticmethod
    def build_validation_evidence(validation_results: list[dict]) -> dict[str, Any]:
        """Build evidence from validation results."""
        passed = sum(1 for r in validation_results if r.get("passed"))
        failed = len(validation_results) - passed
        errors = sum(1 for r in validation_results if not r.get("passed") and r.get("severity") == "error")
        warnings = sum(1 for r in validation_results if not r.get("passed") and r.get("severity") == "warning")

        return {
            "total_rules": len(validation_results),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "warnings": warnings,
            "failed_rules": [r["rule_name"] for r in validation_results if not r.get("passed")],
        }

    @staticmethod
    def build_uncertainty_evidence(
        extraction_data: dict[str, Any],
        validation_results: list[dict],
    ) -> dict[str, Any]:
        """Build uncertainty evidence for decision making."""
        uncertainty_factors = []

        # Check MRZ detection
        if not extraction_data.get("mrz_detected"):
            uncertainty_factors.append("MRZ not detected")

        # Check quality
        quality = extraction_data.get("quality", {})
        if not quality.get("quality_passed", True):
            uncertainty_factors.append("Image quality below threshold")

        # Check validation errors
        errors = [r["rule_name"] for r in validation_results if not r.get("passed") and r.get("severity") == "error"]
        if errors:
            uncertainty_factors.append(f"Validation errors: {', '.join(errors)}")

        # Check OCR confidence
        ocr_engine = extraction_data.get("ocr_engine_used")
        if not ocr_engine:
            uncertainty_factors.append("No OCR engine available")

        return {
            "uncertainty_score": len(uncertainty_factors),
            "uncertainty_factors": uncertainty_factors,
        }
