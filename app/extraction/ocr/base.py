"""Base OCR engine interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseOCREngine(ABC):
    """Abstract base class for OCR engines."""

    @abstractmethod
    def extract_text(self, image_path: Path) -> str:
        """Extract all text from an image."""
        pass

    @abstractmethod
    def extract_text_with_confidence(self, image_path: Path) -> list[dict[str, Any]]:
        """Extract text with confidence scores."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the OCR engine is available."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the OCR engine."""
        pass
