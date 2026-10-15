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
        """Lazy load PaddleOCR (v3 API: no use_angle_cls, uses predict())."""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR  # type: ignore

                # Disable doc unwarping (UVDoc) and orientation classifiers —
                # they crash on some oneDNN builds and aren't needed for flat passport scans.
                self._ocr = PaddleOCR(
                    lang="en",
                    use_doc_unwarping=False,
                    use_doc_orientation_classify=False,
                    use_textline_orientation=False,
                )
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
            import paddleocr  # type: ignore  # noqa: F401
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
        """Extract all text from an image.

        Crops the bottom 25% (MRZ zone) and OCRs it first, then the full page.
        Returns mrz_crop_text + '\\x00' + full_page_text so field_extractor can
        scope its stream scan to the MRZ zone and avoid false positives.
        """
        if not self.is_available():
            raise OCRError("PaddleOCR is not available")

        try:
            import tempfile
            from PIL import Image

            ocr = self._get_ocr()

            def _ocr_lines(path: str) -> list[str]:
                """Extract text lines using PaddleOCR v3 predict() API."""
                result = ocr.predict(path)
                lines: list[str] = []
                for page in result:
                    if page is None:
                        continue
                    # v3 result object exposes rec_texts directly
                    if hasattr(page, "rec_texts"):
                        lines.extend(t for t in page.rec_texts if t)
                    else:
                        # fallback: v2-style nested list [(bbox, (text, score)), ...]
                        for item in page:
                            if item and len(item) >= 2:
                                text_info = item[1]
                                if isinstance(text_info, (list, tuple)) and text_info:
                                    lines.append(text_info[0])
                return lines

            # --- MRZ zone: bottom 25% via a proper temp file ---
            img = Image.open(image_path)
            w, h = img.size
            mrz_crop = img.crop((0, int(h * 0.72), w, h))
            mrz_text = ""
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                mrz_crop.save(tmp.name)
                tmp_path = tmp.name
            try:
                mrz_text = "\n".join(_ocr_lines(tmp_path))
            finally:
                import os; os.unlink(tmp_path)

            # --- Full page ---
            full_text = "\n".join(_ocr_lines(str(image_path)))

            # \x00 separates MRZ-crop text from full-page text
            combined = mrz_text + "\x00" + full_text
            logger.info("Text extracted with PaddleOCR", mrz_chars=len(mrz_text), full_chars=len(full_text))
            logger.debug("PaddleOCR MRZ crop lines", lines=mrz_text[:300])
            logger.debug("PaddleOCR full page lines", lines=full_text[:300])
            return combined
        except Exception as e:
            logger.error("PaddleOCR text extraction failed", error=str(e))
            raise OCRError(f"PaddleOCR extraction failed: {e}") from e

    def extract_text_with_confidence(self, image_path: Path) -> list[dict[str, Any]]:
        """Extract text with confidence scores."""
        if not self.is_available():
            raise OCRError("PaddleOCR is not available")

        try:
            ocr = self._get_ocr()
            result = ocr.predict(str(image_path))

            results = []
            for page in result:
                if page is None:
                    continue
                if hasattr(page, "rec_texts"):
                    boxes = getattr(page, "dt_boxes", [None] * len(page.rec_texts))
                    scores = getattr(page, "rec_scores", [1.0] * len(page.rec_texts))
                    for text, score, bbox in zip(page.rec_texts, scores, boxes):
                        if not text:
                            continue
                        if bbox is not None and len(bbox) == 4:
                            x_coords = [p[0] for p in bbox]
                            y_coords = [p[1] for p in bbox]
                            bbox_dict = {
                                "x": int(min(x_coords)), "y": int(min(y_coords)),
                                "width": int(max(x_coords) - min(x_coords)),
                                "height": int(max(y_coords) - min(y_coords)),
                            }
                        else:
                            bbox_dict = {"x": 0, "y": 0, "width": 0, "height": 0}
                        results.append({"text": text, "confidence": float(score), "bbox": bbox_dict})
                else:
                    for item in page:
                        if item and len(item) >= 2:
                            bbox, text_info = item[0], item[1]
                            text = text_info[0] if text_info else ""
                            confidence = text_info[1] if len(text_info) > 1 else 0.0
                            if bbox and len(bbox) == 4:
                                x_coords = [p[0] for p in bbox]
                                y_coords = [p[1] for p in bbox]
                                bbox_dict = {
                                    "x": int(min(x_coords)), "y": int(min(y_coords)),
                                    "width": int(max(x_coords) - min(x_coords)),
                                    "height": int(max(y_coords) - min(y_coords)),
                                }
                            else:
                                bbox_dict = {"x": 0, "y": 0, "width": 0, "height": 0}
                            results.append({"text": text, "confidence": float(confidence), "bbox": bbox_dict})

            logger.info("Text extracted with confidence", count=len(results))
            return results
        except Exception as e:
            logger.error("PaddleOCR extraction with confidence failed", error=str(e))
            raise OCRError(f"PaddleOCR extraction failed: {e}") from e
