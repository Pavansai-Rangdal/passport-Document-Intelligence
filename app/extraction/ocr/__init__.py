"""OCR engine modules."""

from app.extraction.ocr.base import BaseOCREngine
from app.extraction.ocr.field_extractor import FieldExtractor
from app.extraction.ocr.paddle_ocr import PaddleOCREngine
from app.extraction.ocr.tesseract_ocr import TesseractOCREngine

__all__ = [
    "BaseOCREngine",
    "TesseractOCREngine",
    "PaddleOCREngine",
    "FieldExtractor",
]
