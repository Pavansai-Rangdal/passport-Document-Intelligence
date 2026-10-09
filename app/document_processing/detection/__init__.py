"""Document detection modules."""

from app.document_processing.detection.document_detector import DocumentDetector
from app.document_processing.detection.mrz_detector import MRZDetector

__all__ = [
    "DocumentDetector",
    "MRZDetector",
]
