"""Image quality validation rules."""

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import RuleCategory, ValidationSeverity
from app.validation.result import ValidationResult

logger = get_logger(__name__)

settings = get_settings()


class ImageRules:
    """Image quality validation rules."""

    @staticmethod
    def validate_dimensions(width: int, height: int) -> ValidationResult:
        """Validate image dimensions meet minimum requirements."""
        if width < settings.min_image_width or height < settings.min_image_height:
            return ValidationResult(
                rule_name="image_dimensions",
                rule_category=RuleCategory.IMAGE_QUALITY,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message=f"Image dimensions too small: {width}x{height}",
                details={
                    "actual": {"width": width, "height": height},
                    "minimum": {"width": settings.min_image_width, "height": settings.min_image_height},
                },
            )

        return ValidationResult(
            rule_name="image_dimensions",
            rule_category=RuleCategory.IMAGE_QUALITY,
            severity=ValidationSeverity.INFO,
            passed=True,
            message="Image dimensions meet requirements",
        )

    @staticmethod
    def validate_blur_score(blur_score: float) -> ValidationResult:
        """Validate image is not too blurry."""
        if blur_score > settings.max_blur_score:
            return ValidationResult(
                rule_name="image_blur",
                rule_category=RuleCategory.IMAGE_QUALITY,
                severity=ValidationSeverity.WARNING,
                passed=False,
                message=f"Image appears blurry (score: {blur_score:.2f})",
                details={"blur_score": blur_score, "max_allowed": settings.max_blur_score},
            )

        return ValidationResult(
            rule_name="image_blur",
            rule_category=RuleCategory.IMAGE_QUALITY,
            severity=ValidationSeverity.INFO,
            passed=True,
            message="Image blur score acceptable",
        )

    @staticmethod
    def validate_brightness(brightness: float) -> ValidationResult:
        """Validate image brightness is within acceptable range."""
        if brightness < settings.min_brightness or brightness > settings.max_brightness:
            return ValidationResult(
                rule_name="image_brightness",
                rule_category=RuleCategory.IMAGE_QUALITY,
                severity=ValidationSeverity.WARNING,
                passed=False,
                message=f"Image brightness out of range: {brightness:.2f}",
                details={
                    "brightness": brightness,
                    "min": settings.min_brightness,
                    "max": settings.max_brightness,
                },
            )

        return ValidationResult(
            rule_name="image_brightness",
            rule_category=RuleCategory.IMAGE_QUALITY,
            severity=ValidationSeverity.INFO,
            passed=True,
            message="Image brightness acceptable",
        )

    @staticmethod
    def validate_mrz_detected(mrz_detected: bool) -> ValidationResult:
        """Validate that MRZ was detected."""
        if not mrz_detected:
            return ValidationResult(
                rule_name="mrz_detected",
                rule_category=RuleCategory.IMAGE_QUALITY,
                severity=ValidationSeverity.ERROR,
                passed=False,
                message="MRZ not detected in image",
            )

        return ValidationResult(
            rule_name="mrz_detected",
            rule_category=RuleCategory.IMAGE_QUALITY,
            severity=ValidationSeverity.INFO,
            passed=True,
            message="MRZ detected successfully",
        )
