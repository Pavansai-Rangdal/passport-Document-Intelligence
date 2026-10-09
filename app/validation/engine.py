"""Validation engine that orchestrates all validation rules."""

from typing import Any

from app.core.logging import get_logger
from app.db.models import Document
from app.validation.consistency_rules import ConsistencyRules
from app.validation.date_rules import DateRules
from app.validation.image_rules import ImageRules
from app.validation.mrz_rules import MRZRules
from app.validation.result import ValidationResult
from app.validation.schema_rules import SchemaRules

logger = get_logger(__name__)


class ValidationEngine:
    """Engine for running validation rules on passport data."""

    def __init__(self) -> None:
        self.schema_rules = SchemaRules()
        self.date_rules = DateRules()
        self.image_rules = ImageRules()
        self.mrz_rules = MRZRules()
        self.consistency_rules = ConsistencyRules()

    def validate_document(
        self,
        document: Document,
        extraction_data: dict[str, Any],
    ) -> list[ValidationResult]:
        """Run all validation rules on a document."""
        logger.info("Starting validation", document_id=str(document.id))
        results: list[ValidationResult] = []

        # Image quality rules
        if document.width and document.height:
            results.append(self.image_rules.validate_dimensions(document.width, document.height))
        if document.blur_score is not None:
            results.append(self.image_rules.validate_blur_score(document.blur_score))
        if document.brightness is not None:
            results.append(self.image_rules.validate_brightness(document.brightness))
        results.append(self.image_rules.validate_mrz_detected(document.mrz_detected))

        # MRZ rules
        mrz_data = extraction_data.get("mrz_data")
        results.append(self.mrz_rules.validate_mrz_present(mrz_data))
        if mrz_data and extraction_data.get("mrz_text"):
            results.append(self.mrz_rules.validate_check_digits(extraction_data["mrz_text"]))

        # Schema rules
        if mrz_data:
            if mrz_data.get("document_number"):
                results.append(self.schema_rules.validate_document_number(mrz_data["document_number"]))
            if mrz_data.get("issuing_state"):
                results.append(self.schema_rules.validate_country_code(mrz_data["issuing_state"]))
            if mrz_data.get("sex"):
                results.append(self.schema_rules.validate_sex(mrz_data["sex"]))
            if mrz_data.get("birth_date"):
                results.append(self.schema_rules.validate_date_format(mrz_data["birth_date"], "birth_date"))
            if mrz_data.get("expiry_date"):
                results.append(self.schema_rules.validate_date_format(mrz_data["expiry_date"], "expiry_date"))

        # Date rules
        if mrz_data:
            if mrz_data.get("expiry_date_normalized"):
                results.append(self.date_rules.validate_not_expired(mrz_data["expiry_date_normalized"]))
            if mrz_data.get("birth_date_normalized"):
                results.append(self.date_rules.validate_reasonable_birth_date(mrz_data["birth_date_normalized"]))

        # Consistency rules
        if mrz_data:
            results.append(
                self.consistency_rules.validate_nationality_issuing_state_match(
                    mrz_data.get("nationality"),
                    mrz_data.get("issuing_state"),
                )
            )
            results.append(
                self.consistency_rules.validate_birth_date_before_expiry(
                    mrz_data.get("birth_date_normalized"),
                    mrz_data.get("expiry_date_normalized"),
                )
            )

        # VIZ/MRZ consistency
        ocr_fields = extraction_data.get("ocr_fields", {})
        normalized_fields = extraction_data.get("normalized_fields", {})
        if ocr_fields.get("document_number") and mrz_data and mrz_data.get("document_number"):
            results.append(
                self.consistency_rules.validate_viz_mrz_consistency(
                    normalized_fields.get("document_number"),
                    mrz_data["document_number"],
                )
            )

        # Log summary
        error_count = sum(1 for r in results if not r.passed and r.severity.value == "error")
        warning_count = sum(1 for r in results if not r.passed and r.severity.value == "warning")

        logger.info(
            "Validation completed",
            document_id=str(document.id),
            total_rules=len(results),
            errors=error_count,
            warnings=warning_count,
        )

        return results

    def get_summary(self, results: list[ValidationResult]) -> dict[str, Any]:
        """Get validation summary."""
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        errors = sum(1 for r in results if not r.passed and r.severity.value == "error")
        warnings = sum(1 for r in results if not r.passed and r.severity.value == "warning")

        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "warnings": warnings,
            "overall_passed": errors == 0,
        }
