"""Document boundary detection using OpenCV."""

from pathlib import Path
from typing import Any

import cv2

from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentDetector:
    """Detects document boundaries in images."""

    @staticmethod
    def detect_boundaries(image_path: Path) -> dict[str, Any]:
        """Detect document boundaries in an image."""
        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError("Failed to load image")

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)

            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Find the largest contour (likely the document)
            if not contours:
                logger.warning("No contours found in image")
                return {"detected": False, "reason": "No contours found"}

            largest_contour = max(contours, key=cv2.contourArea)

            # Approximate the contour to a polygon
            epsilon = 0.02 * cv2.arcLength(largest_contour, True)
            approx = cv2.approxPolyDP(largest_contour, epsilon, True)

            # Check if it's a quadrilateral (document)
            if len(approx) != 4:
                logger.warning("Largest contour is not a quadrilateral", vertices=len(approx))
                return {"detected": False, "reason": "Not a quadrilateral"}

            # Get the bounding rectangle
            x, y, w, h = cv2.boundingRect(approx)

            logger.info(
                "Document boundary detected",
                x=x,
                y=y,
                width=w,
                height=h,
                confidence=cv2.contourArea(largest_contour) / (image.shape[0] * image.shape[1]),
            )

            return {
                "detected": True,
                "bounding_box": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                "vertices": [int(point[0][0]) for point in approx.reshape(-1, 2)],
                "area_ratio": float(cv2.contourArea(largest_contour) / (image.shape[0] * image.shape[1])),
            }
        except Exception as e:
            logger.error("Document detection failed", error=str(e))
            return {"detected": False, "reason": str(e)}

    @staticmethod
    def crop_to_document(image_path: Path, output_path: Path, bounding_box: dict[str, int]) -> bool:
        """Crop image to document boundaries."""
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError("Failed to load image")

            x = bounding_box["x"]
            y = bounding_box["y"]
            w = bounding_box["width"]
            h = bounding_box["height"]

            # Ensure bounds are within image
            x = max(0, x)
            y = max(0, y)
            w = min(w, image.shape[1] - x)
            h = min(h, image.shape[0] - y)

            cropped = image[y : y + h, x : x + w]
            cv2.imwrite(str(output_path), cropped)

            logger.info("Image cropped to document", output_path=str(output_path))
            return True
        except Exception as e:
            logger.error("Failed to crop image", error=str(e))
            return False
