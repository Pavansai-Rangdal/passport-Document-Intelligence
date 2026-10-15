"""OCR engine modules."""

from app.extraction.ocr.base import BaseOCREngine
from app.extraction.ocr.easyocr_engine import EasyOCREngine
from app.extraction.ocr.field_extractor import FieldExtractor
from app.extraction.ocr.paddle_ocr import PaddleOCREngine

__all__ = [
    "BaseOCREngine",
    "PaddleOCREngine",
    "EasyOCREngine",
    "FieldExtractor",
]
