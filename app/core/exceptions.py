"""Custom exceptions."""

from typing import Any


class ApplicationError(Exception):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ExtractionError(ApplicationError):
    pass


class OCRError(ExtractionError):
    pass


class MRZError(ExtractionError):
    pass
