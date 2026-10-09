"""Extraction service orchestrating OCR and MRZ parsing."""

from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import ExtractionError, OCRError
from app.core.logging import get_logger
from app.document_processing.detection import MRZDetector
from app.document_processing.preprocessing import QualityAssessor
from app.extraction.mrz import MRZParser
from app.extraction.normalization import DateNormalizer, FieldNormalizer
from app.extraction.ocr import FieldExtractor, PaddleOCREngine, TesseractOCREngine

logger = get_logger(__name__)

settings = get_settings()


class ExtractionService:
    """Service for extracting passport data from images."""

    def __init__(self) -> None:
        self.tesseract = TesseractOCREngine()
        self.paddle = PaddleOCREngine()
        self.mrz_detector = MRZDetector()
        self.field_extractor = FieldExtractor()
        self.mrz_parser = MRZParser()
        self.date_normalizer = DateNormalizer()
        self.field_normalizer = FieldNormalizer()

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

        # OCR extraction
        ocr_text = ""
        ocr_engine = None

        if settings.ocr_engine in ("tesseract", "both"):
            if self.tesseract.is_available():
                try:
                    ocr_text = self.tesseract.extract_text(image_path)
                    ocr_engine = "tesseract"
                    logger.info("Tesseract OCR completed")
                except OCRError as e:
                    logger.warning("Tesseract OCR failed", error=str(e))

        if settings.ocr_engine in ("paddle", "both") and not ocr_text:
            if self.paddle.is_available():
                try:
                    ocr_text = self.paddle.extract_text(image_path)
                    ocr_engine = "paddle"
                    logger.info("PaddleOCR completed")
                except OCRError as e:
                    logger.warning("PaddleOCR failed", error=str(e))

        if not ocr_text:
            raise ExtractionError("No OCR engine available or extraction failed")

        result["ocr_engine_used"] = ocr_engine

        # Extract MRZ from OCR text
        mrz_lines = self.field_extractor.extract_mrz_lines(ocr_text)
        if mrz_lines:
            try:
                mrz_data = self.mrz_parser.auto_parse("\n".join(mrz_lines))
                mrz_dict = mrz_data.to_dict()

                # Normalize dates
                if mrz_dict.get("birth_date"):
                    mrz_dict["birth_date_normalized"] = self.date_normalizer.normalize(mrz_dict["birth_date"])
                if mrz_dict.get("expiry_date"):
                    mrz_dict["expiry_date_normalized"] = self.date_normalizer.normalize(mrz_dict["expiry_date"])

                result["mrz_data"] = mrz_dict
                result["mrz_detected"] = True
                logger.info("MRZ parsed successfully", mrz_type=mrz_data.mrz_type)
            except Exception as e:
                logger.warning("MRZ parsing failed", error=str(e))

        # Extract fields from OCR text
        try:
            ocr_fields = self.field_extractor.extract_fields(ocr_text)
            result["ocr_fields"] = ocr_fields

            # Normalize fields
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

    def benchmark_ocr_engines(self, image_path: Path) -> dict[str, Any]:
        """Benchmark both OCR engines on an image."""
        logger.info("Benchmarking OCR engines", image_path=str(image_path))

        results = {
            "tesseract": {"available": False, "text": "", "time_ms": 0},
            "paddle": {"available": False, "text": "", "time_ms": 0},
        }

        import time

        # Benchmark Tesseract
        if self.tesseract.is_available():
            try:
                start = time.time()
                text = self.tesseract.extract_text(image_path)
                elapsed = (time.time() - start) * 1000
                results["tesseract"] = {
                    "available": True,
                    "text": text,
                    "time_ms": elapsed,
                    "text_length": len(text),
                }
                logger.info("Tesseract benchmark completed", time_ms=elapsed)
            except Exception as e:
                logger.warning("Tesseract benchmark failed", error=str(e))

        # Benchmark PaddleOCR
        if self.paddle.is_available():
            try:
                start = time.time()
                text = self.paddle.extract_text(image_path)
                elapsed = (time.time() - start) * 1000
                results["paddle"] = {
                    "available": True,
                    "text": text,
                    "time_ms": elapsed,
                    "text_length": len(text),
                }
                logger.info("PaddleOCR benchmark completed", time_ms=elapsed)
            except Exception as e:
                logger.warning("PaddleOCR benchmark failed", error=str(e))

        return results
