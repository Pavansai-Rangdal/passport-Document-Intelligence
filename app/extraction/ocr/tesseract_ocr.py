"""Tesseract OCR engine implementation."""

from pathlib import Path
from typing import Any

from app.core.exceptions import OCRError
from app.core.logging import get_logger
from app.extraction.ocr.base import BaseOCREngine

logger = get_logger(__name__)


class TesseractOCREngine(BaseOCREngine):
    """Tesseract OCR engine implementation."""

    def __init__(self) -> None:
        self._available: bool | None = None

    def is_available(self) -> bool:
        """Check if Tesseract is available."""
        if self._available is not None:
            return self._available

        try:
            import pytesseract

            # Try to get version to verify installation
            pytesseract.get_tesseract_version()
            self._available = True
            logger.info("Tesseract OCR is available")
            return True
        except Exception as e:
            logger.warning("Tesseract OCR is not available", error=str(e))
            self._available = False
            return False

    def get_name(self) -> str:
        """Get the engine name."""
        return "tesseract"

    def extract_text(self, image_path: Path) -> str:
        """Extract all text from an image."""
        if not self.is_available():
            raise OCRError("Tesseract OCR is not available")

        try:
            import pytesseract

            text = pytesseract.image_to_string(str(image_path), lang="eng")
            logger.info("Text extracted with Tesseract", length=len(text))
            return text
        except Exception as e:
            logger.error("Tesseract text extraction failed", error=str(e))
            raise OCRError(f"Tesseract extraction failed: {e}") from e

    def extract_text_with_confidence(self, image_path: Path) -> list[dict[str, Any]]:
        """Extract text with confidence scores."""
        if not self.is_available():
            raise OCRError("Tesseract OCR is not available")

        try:
            import pytesseract

            data = pytesseract.image_to_data(
                str(image_path),
                lang="eng",
                output_type=pytesseract.Output.DICT,
            )

            results = []
            for i in range(len(data["text"])):
                if data["text"][i].strip():
                    results.append(
                        {
                            "text": data["text"][i],
                            "confidence": float(data["conf"][i]) / 100.0,
                            "bbox": {
                                "x": data["left"][i],
                                "y": data["top"][i],
                                "width": data["width"][i],
                                "height": data["height"][i],
                            },
                        }
                    )

            logger.info("Text extracted with confidence", count=len(results))
            return results
        except Exception as e:
            logger.error("Tesseract extraction with confidence failed", error=str(e))
            raise OCRError(f"Tesseract extraction failed: {e}") from e
