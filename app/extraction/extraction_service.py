"""Extraction service orchestrating OCR and MRZ parsing."""

from pathlib import Path
from typing import Any

from PIL import Image

from app.core.config import get_settings
from app.core.exceptions import ExtractionError, OCRError
from app.core.logging import get_logger
from app.document_processing.detection import MRZDetector
from app.document_processing.preprocessing import QualityAssessor
from app.extraction.mrz import MRZParser
from app.extraction.normalization import DateNormalizer, FieldNormalizer
from app.extraction.ocr import EasyOCREngine, FieldExtractor, PaddleOCREngine

logger = get_logger(__name__)

settings = get_settings()

# MRZ strip tried first (bottom 28% of the page), then a taller one for cropped/odd layouts
_MRZ_TOP_FRACTIONS = (0.72, 0.5)
_MRZ_STRIP_MAX_WIDTH = 1000


class ExtractionService:
    """Service for extracting passport data from images."""

    def __init__(self) -> None:
        self.paddle = PaddleOCREngine()
        self.easyocr = EasyOCREngine()
        self.mrz_detector = MRZDetector()
        self.field_extractor = FieldExtractor()
        self.mrz_parser = MRZParser()
        self.date_normalizer = DateNormalizer()
        self.field_normalizer = FieldNormalizer()

    @staticmethod
    def _mrz_strip(image_path: Path, top_fraction: float) -> Image.Image:
        """Bottom of the page from top_fraction down (the MRZ zone), downscaled so OCR cost doesn't grow with photo size."""
        with Image.open(image_path) as img:
            w, h = img.size
            strip = img.crop((0, int(h * top_fraction), w, h)).convert("RGB")
        if strip.width > _MRZ_STRIP_MAX_WIDTH:
            ratio = _MRZ_STRIP_MAX_WIDTH / strip.width
            strip = strip.resize((_MRZ_STRIP_MAX_WIDTH, max(1, int(strip.height * ratio))))
        return strip

    def extract_from_image(self, image_path: Path) -> dict[str, Any]:
        """Extract all passport data from an image."""
        logger.info("Starting extraction", image_path=str(image_path))

        result = {
            "image_path": str(image_path),
            "mrz_detected": False,
            "mrz_data": None,
            "ocr_fields": {},
            "normalized_fields": {},
            "quality": None,
            "ocr_engine_used": None,
        }

        # Assess quality first
        try:
            quality = QualityAssessor.overall_quality_assessment(image_path)
            result["quality"] = quality
            logger.info("Quality assessment completed", quality_passed=quality["quality_passed"])
        except Exception as e:
            logger.warning("Quality assessment failed", error=str(e))

        # Detect MRZ
        try:
            mrz_detection = self.mrz_detector.detect_mrz(image_path)
            result["mrz_detected"] = mrz_detection["detected"]
            if mrz_detection["detected"]:
                logger.info("MRZ detected", bbox=mrz_detection["bounding_box"])
        except Exception as e:
            logger.warning("MRZ detection failed", error=str(e))

        def _try_parse_mrz(text: str) -> dict | None:
            from app.extraction.mrz.check_digits import MRZCheckDigitValidator

            lines = self.field_extractor.extract_mrz_lines(text)
            if not lines:
                return None
            try:
                mrz_data = self.mrz_parser.auto_parse("\n".join(lines))
                mrz_dict = mrz_data.to_dict()
                if mrz_dict.get("birth_date"):
                    mrz_dict["birth_date_normalized"] = self.date_normalizer.normalize(mrz_dict["birth_date"])
                if mrz_dict.get("expiry_date"):
                    mrz_dict["expiry_date_normalized"] = self.date_normalizer.normalize(mrz_dict["expiry_date"])

                # Score check digits — gives a real 0.0–1.0 confidence signal.
                # Use correct ICAO positions directly for the 3 individual TD3 checks.
                check_score: float | None = None
                try:
                    if mrz_data.mrz_type == "TD3" and len(lines) == 2 and len(lines[1]) == 44:
                        l2 = lines[1]
                        checks = [
                            MRZCheckDigitValidator.validate_check_digit(l2[0:9], l2[9]),   # doc number
                            MRZCheckDigitValidator.validate_check_digit(l2[13:19], l2[19]),  # birth date
                            MRZCheckDigitValidator.validate_check_digit(l2[21:27], l2[27]),  # expiry date
                        ]
                        check_score = sum(checks) / len(checks)
                    elif mrz_data.mrz_type == "TD1" and len(lines) == 3:
                        l1, l2 = lines[0], lines[1]
                        checks = [
                            MRZCheckDigitValidator.validate_check_digit(l1[5:14], l1[14]),   # doc number
                            MRZCheckDigitValidator.validate_check_digit(l2[0:6], l2[6]),     # birth date
                            MRZCheckDigitValidator.validate_check_digit(l2[8:14], l2[14]),   # expiry date
                        ]
                        check_score = sum(checks) / len(checks)
                    elif mrz_data.mrz_type == "TD2" and len(lines) == 2 and len(lines[1]) == 36:
                        l2 = lines[1]
                        checks = [
                            MRZCheckDigitValidator.validate_check_digit(l2[0:9], l2[9]),    # doc number
                            MRZCheckDigitValidator.validate_check_digit(l2[13:19], l2[19]), # birth date
                            MRZCheckDigitValidator.validate_check_digit(l2[21:27], l2[27]), # expiry date
                        ]
                        check_score = sum(checks) / len(checks)
                except Exception:
                    pass

                mrz_dict["check_digit_score"] = check_score
                logger.info("MRZ parsed successfully", mrz_type=mrz_data.mrz_type, check_score=check_score)
                return mrz_dict
            except Exception as e:
                logger.warning("MRZ parsing failed", error=str(e))
                return None

        def _score(mrz: dict) -> float:
            return mrz.get("check_digit_score") or 0.0

        # --- Fast path: OCR only the MRZ strip. EasyOCR reads (fast), PaddleOCR re-reads
        # (accurate) only if the MRZ check digits don't all pass. ---
        ocr_text = ""
        ocr_engine = None
        mrz_dict = None
        for top_fraction in _MRZ_TOP_FRACTIONS:
            if mrz_dict is not None:
                break
            try:
                strip = self._mrz_strip(image_path, top_fraction)
            except Exception as e:
                logger.warning("MRZ strip crop failed", error=str(e))
                break

            for engine in (self.easyocr, self.paddle):
                if not engine.is_available():
                    continue
                try:
                    text = engine.extract_mrz_text(strip)
                except OCRError as e:
                    logger.warning("MRZ strip OCR failed", engine=engine.get_name(), error=str(e))
                    continue
                parsed = _try_parse_mrz(text)
                if parsed and (mrz_dict is None or _score(parsed) > _score(mrz_dict)):
                    mrz_dict, ocr_text, ocr_engine = parsed, text, engine.get_name()
                if mrz_dict and _score(mrz_dict) >= 1.0:
                    break

        # --- Slow fallback (only if the strip gave no MRZ): full-page OCR, PaddleOCR then EasyOCR ---
        if mrz_dict is None:
            ocr_text = ""
            ocr_engine = None

            if self.paddle.is_available():
                try:
                    ocr_text = self.paddle.extract_text(image_path)
                    ocr_engine = "paddle"
                    logger.info("PaddleOCR completed")
                except OCRError as e:
                    logger.warning("PaddleOCR failed", error=str(e))

            if not ocr_text and self.easyocr.is_available():
                try:
                    ocr_text = self.easyocr.extract_text(image_path)
                    ocr_engine = "easyocr"
                    logger.info("EasyOCR completed")
                except OCRError as e:
                    logger.warning("EasyOCR failed", error=str(e))

            if not ocr_text:
                raise ExtractionError("No OCR engine produced output")

            # Try MRZ from primary OCR
            mrz_dict = _try_parse_mrz(ocr_text)

            # If PaddleOCR got text but MRZ parsing failed, retry with EasyOCR
            if mrz_dict is None and ocr_engine == "paddle" and self.easyocr.is_available():
                logger.info("PaddleOCR MRZ parse failed — retrying with EasyOCR")
                try:
                    easy_text = self.easyocr.extract_text(image_path)
                    if easy_text:
                        mrz_dict = _try_parse_mrz(easy_text)
                        if mrz_dict:
                            ocr_text = easy_text
                            ocr_engine = "easyocr"
                except Exception as e:
                    logger.warning("EasyOCR fallback failed", error=str(e))

        result["ocr_engine_used"] = ocr_engine

        if mrz_dict is not None:
            result["mrz_data"] = mrz_dict
            result["mrz_detected"] = True

        # Extract visible fields from OCR text
        try:
            ocr_fields = self.field_extractor.extract_fields(ocr_text)
            result["ocr_fields"] = ocr_fields

            normalized = {}
            for field_name, value in ocr_fields.items():
                if field_name in ("document_number", "passport_number"):
                    normalized[field_name] = self.field_normalizer.normalize_document_number(value)
                elif field_name in ("surname", "given_names"):
                    normalized[field_name] = self.field_normalizer.normalize_name(value)
                elif field_name in ("nationality", "issuing_state"):
                    normalized[field_name] = self.field_normalizer.normalize_country_code(value)
                elif field_name == "sex":
                    normalized[field_name] = self.field_normalizer.normalize_sex(value)
                elif "date" in field_name:
                    normalized[field_name] = self.date_normalizer.normalize(value)
                else:
                    normalized[field_name] = self.field_normalizer.clean_whitespace(value)

            result["normalized_fields"] = normalized
            logger.info("Fields extracted and normalized", count=len(normalized))
        except Exception as e:
            logger.warning("Field extraction failed", error=str(e))

        logger.info("Extraction completed", mrz_detected=result["mrz_detected"])
        return result
