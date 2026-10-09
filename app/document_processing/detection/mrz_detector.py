"""MRZ (Machine Readable Zone) detection in passport images."""

from pathlib import Path
from typing import Any

import cv2

from app.core.logging import get_logger

logger = get_logger(__name__)


class MRZDetector:
    """Detects MRZ (Machine Readable Zone) in passport images."""

    @staticmethod
    def detect_mrz(image_path: Path) -> dict[str, Any]:
        """Detect MRZ region in passport image."""
        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError("Failed to load image")

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply threshold to get binary image
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Apply morphological operations to connect text regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 3))
            morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            # Find contours
            contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filter contours to find MRZ-like regions
            mrz_candidates = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                # MRZ characteristics:
                # - Located at bottom of passport
                # - Wide and relatively short
                # - Aspect ratio typically > 5:1
                aspect_ratio = w / h if h > 0 else 0

                if aspect_ratio > 5 and aspect_ratio < 15 and h > 20 and h < 60:
                    # Check if it's in the bottom third of the image
                    if y > image.shape[0] * 0.6:
                        mrz_candidates.append({"x": x, "y": y, "w": w, "h": h, "area": w * h})

            if not mrz_candidates:
                logger.warning("No MRZ candidates found")
                return {"detected": False, "reason": "No MRZ candidates found"}

            # Select the largest candidate
            best_candidate = max(mrz_candidates, key=lambda c: c["area"])

            logger.info(
                "MRZ detected",
                x=best_candidate["x"],
                y=best_candidate["y"],
                width=best_candidate["w"],
                height=best_candidate["h"],
            )

            return {
                "detected": True,
                "bounding_box": {
                    "x": best_candidate["x"],
                    "y": best_candidate["y"],
                    "width": best_candidate["w"],
                    "height": best_candidate["h"],
                },
            }
        except Exception as e:
            logger.error("MRZ detection failed", error=str(e))
            return {"detected": False, "reason": str(e)}

    @staticmethod
    def extract_mrz_region(image_path: Path, bounding_box: dict[str, int]) -> str:
        """Extract MRZ text from the detected region using OCR-like methods."""
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError("Failed to load image")

            x = bounding_box["x"]
            y = bounding_box["y"]
            w = bounding_box["width"]
            h = bounding_box["height"]

            # Extract MRZ region
            mrz_region = image[y : y + h, x : x + w]

            # Convert to grayscale
            gray = cv2.cvtColor(mrz_region, cv2.COLOR_BGR2GRAY)

            # Apply threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Note: This is a placeholder - actual OCR would be done by the OCR engines
            # For now, we return the bounding box info for the OCR engines to process
            logger.info("MRZ region extracted for OCR processing")
            return "MRZ_REGION_EXTRACTED"
        except Exception as e:
            logger.error("Failed to extract MRZ region", error=str(e))
            raise
