"""Custom exceptions for the application."""

from typing import Any


class ApplicationError(Exception):
    """Base exception for application errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ValidationError(ApplicationError):
    """Raised when validation fails."""

    pass


class ExtractionError(ApplicationError):
    """Raised when extraction fails."""

    pass


class OCRError(ExtractionError):
    """Raised when OCR processing fails."""

    pass


class MRZError(ExtractionError):
    """Raised when MRZ parsing fails."""

    pass


class VerificationError(ApplicationError):
    """Raised when verification fails."""

    pass


class SecurityError(ApplicationError):
    """Raised when security violations occur."""

    pass


class FileIntakeError(ApplicationError):
    """Raised when file intake fails."""

    pass


class DatabaseError(ApplicationError):
    """Raised when database operations fail."""

    pass
