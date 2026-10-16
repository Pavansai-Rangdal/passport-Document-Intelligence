"""EasyOCR engine — deep-learning OCR, no external binary required."""

from pathlib import Path
from typing import Any

from app.core.exceptions import OCRError
from app.core.logging import get_logger
from app.extraction.ocr.base import BaseOCREngine

logger = get_logger(__name__)


class EasyOCREngine(BaseOCREngine):
    """EasyOCR engine: deep-learning OCR that handles real-world document images well."""

    def __init__(self) -> None:
        self._reader = None
        self._available: bool | None = None

    def _get_reader(self):
        if self._reader is None:
            import easyocr
            logger.info("Initialising EasyOCR reader (first-time model load)")
            self._reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        return self._reader

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import easyocr  # noqa: F401
            self._available = True
            logger.info("EasyOCR is available")
        except ImportError:
            self._available = False
            logger.warning("EasyOCR is not available", error="No module named 'easyocr'")
        return self._available

    def get_name(self) -> str:
        return "easyocr"

    def extract_text(self, image_path: Path) -> str:
        """Extract text from image using EasyOCR.

        Crops the bottom 28% (MRZ zone) separately and uses an MRZ-char allowlist
        on that crop to reduce misreadings. Returns mrz_crop_text + '\\x00' + full_text
        so field_extractor can scope its stream scan to the MRZ zone.
        """
        if not self.is_available():
            raise OCRError("EasyOCR is not available")

        try:
            import numpy as np
            from PIL import Image

            reader = self._get_reader()
            MRZ_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"

            img = Image.open(image_path)
            w, h = img.size
            mrz_pil = img.crop((0, int(h * 0.72), w, h))
            mrz_arr = np.array(mrz_pil)

            mrz_results = reader.readtext(
                mrz_arr,
                detail=0,
                paragraph=False,
                allowlist=MRZ_CHARS,
                width_ths=0.3,
            )
            mrz_text = "\n".join(str(r) for r in mrz_results)

            full_results = reader.readtext(str(image_path), detail=0, paragraph=False)
            full_text = "\n".join(str(r) for r in full_results)

            logger.info("Text extracted with EasyOCR", length=len(full_text))
            return mrz_text + "\x00" + full_text
        except Exception as e:
            logger.error("EasyOCR extraction failed", error=str(e))
            raise OCRError(f"EasyOCR extraction failed: {e}") from e

    def extract_text_with_confidence(self, image_path: Path) -> list[dict[str, Any]]:
        """Extract text with bounding boxes and confidence scores."""
        if not self.is_available():
            raise OCRError("EasyOCR is not available")

        try:
            reader = self._get_reader()
            raw = reader.readtext(str(image_path))
            return [
                {
                    "text": item[1],
                    "confidence": float(item[2]),
                    "bbox": {
                        "x": int(item[0][0][0]),
                        "y": int(item[0][0][1]),
                        "width": int(item[0][2][0] - item[0][0][0]),
                        "height": int(item[0][2][1] - item[0][0][1]),
                    },
                }
                for item in raw
            ]
        except Exception as e:
            logger.error("EasyOCR extraction with confidence failed", error=str(e))
            raise OCRError(f"EasyOCR extraction failed: {e}") from e
