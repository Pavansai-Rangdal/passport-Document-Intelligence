"""Image quality assessment."""

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()


class QualityAssessor:
    """Assesses image quality for document processing."""

    @staticmethod
    def assess_blur(image: np.ndarray) -> float:
        """Assess image blur using Laplacian variance."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            return float(laplacian_var)
        except Exception as e:
            logger.error("Failed to assess blur", error=str(e))
            return 0.0

    @staticmethod
    def assess_brightness(image: np.ndarray) -> float:
        """Assess image brightness (mean pixel value)."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            brightness = float(np.mean(gray))
            return brightness
        except Exception as e:
            logger.error("Failed to assess brightness", error=str(e))
            return 0.0

    @staticmethod
    def assess_contrast(image: np.ndarray) -> float:
        """Assess image contrast (standard deviation)."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            contrast = float(np.std(gray))
            return contrast
        except Exception as e:
            logger.error("Failed to assess contrast", error=str(e))
            return 0.0

    @staticmethod
    def assess_noise(image: np.ndarray) -> float:
        """Assess image noise using local standard deviation."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Use Laplacian as a simple noise indicator
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            noise = float(np.std(laplacian))
            return noise
        except Exception as e:
            logger.error("Failed to assess noise", error=str(e))
            return 0.0

    @staticmethod
    def overall_quality_assessment(image_path: Path) -> dict[str, Any]:
        """Perform overall quality assessment."""
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError("Failed to load image")

            height, width = image.shape[:2]

            # Assess various quality metrics
            blur_score = QualityAssessor.assess_blur(image)
            brightness = QualityAssessor.assess_brightness(image)
            contrast = QualityAssessor.assess_contrast(image)
            noise = QualityAssessor.assess_noise(image)

            # Determine if quality passes thresholds
            quality_passed = (
                width >= settings.min_image_width
                and height >= settings.min_image_height
                and blur_score <= settings.max_blur_score
                and settings.min_brightness <= brightness <= settings.max_brightness
            )

            result = {
                "width": width,
                "height": height,
                "blur_score": blur_score,
                "brightness": brightness,
                "contrast": contrast,
                "noise": noise,
                "quality_passed": quality_passed,
                "thresholds": {
                    "min_width": settings.min_image_width,
                    "min_height": settings.min_image_height,
                    "max_blur": settings.max_blur_score,
                    "min_brightness": settings.min_brightness,
                    "max_brightness": settings.max_brightness,
                },
            }

            logger.info("Quality assessment completed", quality_passed=quality_passed)
            return result
        except Exception as e:
            logger.error("Quality assessment failed", error=str(e))
            raise
