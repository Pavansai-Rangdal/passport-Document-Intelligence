"""PaddleOCR engine implementation."""

from pathlib import Path
from typing import Any

from app.core.exceptions import OCRError
from app.core.logging import get_logger
from app.extraction.ocr.base import BaseOCREngine

logger = get_logger(__name__)


class PaddleOCREngine(BaseOCREngine):
    """PaddleOCR engine implementation."""

    def __init__(self) -> None:
        self._ocr: Any = None
        self._available: bool | None = None

    def _get_ocr(self) -> Any:
        """Lazy load PaddleOCR."""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR  # type: ignore

                self._ocr = PaddleOCR(use_angle_cls=True, lang="en")
                logger.info("PaddleOCR initialized")
            except Exception as e:
                logger.error("Failed to initialize PaddleOCR", error=str(e))
                raise OCRError(f"PaddleOCR initialization failed: {e}") from e
        return self._ocr

    def is_available(self) -> bool:
        """Check if PaddleOCR is available."""
        if self._available is not None:
            return self._available

        try:
            from paddleocr import PaddleOCR  # type: ignore

            # Try to create a minimal instance to verify
            _ = PaddleOCR(use_angle_cls=True, lang="en")
            self._available = True
            logger.info("PaddleOCR is available")
            return True
        except Exception as e:
            logger.warning("PaddleOCR is not available", error=str(e))
            self._available = False
            return False

    def get_name(self) -> str:
        """Get the engine name."""
        return "paddle"

    def extract_text(self, image_path: Path) -> str:
        """Extract all text from an image."""
        if not self.is_available():
            raise OCRError("PaddleOCR is not available")

        try:
            ocr = self._get_ocr()
            result = ocr.ocr(str(image_path), cls=True)

            if not result or not result[0]:
                logger.warning("No text detected by PaddleOCR")
                return ""

            # Extract text from results
            text_lines = []
            for line in result[0]:
                if line and len(line) >= 2:
                    text_lines.append(line[1][0])

            text = "\n".join(text_lines)
            logger.info("Text extracted with PaddleOCR", length=len(text))
            return text
        except Exception as e:
            logger.error("PaddleOCR text extraction failed", error=str(e))
            raise OCRError(f"PaddleOCR extraction failed: {e}") from e

    def extract_text_with_confidence(self, image_path: Path) -> list[dict[str, Any]]:
        """Extract text with confidence scores."""
        if not self.is_available():
            raise OCRError("PaddleOCR is not available")

        try:
            ocr = self._get_ocr()
            result = ocr.ocr(str(image_path), cls=True)

            if not result or not result[0]:
                logger.warning("No text detected by PaddleOCR")
                return []

            # Extract text with confidence
            results = []
            for line in result[0]:
                if line and len(line) >= 2:
                    bbox = line[0]
                    text_info = line[1]
                    text = text_info[0]
                    confidence = text_info[1] if len(text_info) > 1 else 0.0

                    # Convert bbox to simple format
                    if isinstance(bbox, list) and len(bbox) == 4:
                        x_coords = [point[0] for point in bbox]
                        y_coords = [point[1] for point in bbox]
                        bbox_dict = {
                            "x": int(min(x_coords)),
                            "y": int(min(y_coords)),
                            "width": int(max(x_coords) - min(x_coords)),
                            "height": int(max(y_coords) - min(y_coords)),
                        }
                    else:
                        bbox_dict = {"x": 0, "y": 0, "width": 0, "height": 0}

                    results.append(
                        {
                            "text": text,
                            "confidence": float(confidence),
                            "bbox": bbox_dict,
                        }
                    )

            logger.info("Text extracted with confidence", count=len(results))
            return results
        except Exception as e:
            logger.error("PaddleOCR extraction with confidence failed", error=str(e))
            raise OCRError(f"PaddleOCR extraction failed: {e}") from e
