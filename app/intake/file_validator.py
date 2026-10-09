"""File validation for uploaded documents."""

from pathlib import Path
from typing import Literal

import filetype

from app.core.config import get_settings
from app.core.exceptions import FileIntakeError, SecurityError
from app.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()


class FileValidator:
    """Validates uploaded files for security and format compliance."""

    @staticmethod
    def validate_mime_type(file_path: Path) -> str:
        """Validate file MIME type and return it."""
        try:
            kind = filetype.guess(str(file_path))
            if kind is None:
                raise FileIntakeError("Unable to determine file type")

            mime_type = kind.mime
            if mime_type not in settings.storage_allowed_mime_types:
                raise SecurityError(
                    f"File type {mime_type} not allowed. Allowed types: {settings.storage_allowed_mime_types}"
                )

            logger.info("File MIME type validated", mime_type=mime_type)
            return mime_type
        except Exception as e:
            logger.error("MIME type validation failed", error=str(e))
            raise FileIntakeError(f"Failed to validate file type: {e}") from e

    @staticmethod
    def validate_file_size(file_size: int) -> None:
        """Validate file size against limits."""
        if file_size > settings.storage_max_file_size:
            raise SecurityError(
                f"File size {file_size} bytes exceeds maximum allowed size {settings.storage_max_file_size} bytes"
            )
        if file_size == 0:
            raise FileIntakeError("File is empty")

        logger.info("File size validated", size_bytes=file_size)

    @staticmethod
    def validate_file_integrity(file_path: Path) -> Literal[True]:
        """Validate file integrity (basic checks)."""
        if not file_path.exists():
            raise FileIntakeError(f"File does not exist: {file_path}")

        if not file_path.is_file():
            raise FileIntakeError(f"Path is not a file: {file_path}")

        try:
            # Try to read the file to ensure it's accessible
            with open(file_path, "rb") as f:
                f.read(1)
        except Exception as e:
            raise FileIntakeError(f"File is not readable: {e}") from e

        logger.info("File integrity validated", file_path=str(file_path))
        return True

    @staticmethod
    def detect_malformed_file(file_path: Path, mime_type: str) -> bool:
        """Detect malformed or corrupted files."""
        try:
            if mime_type == "application/pdf":
                import pymupdf  # PyMuPDF

                doc = pymupdf.open(str(file_path))
                page_count = doc.page_count
                doc.close()

                if page_count == 0:
                    raise FileIntakeError("PDF has no pages")

                logger.info("PDF validated", page_count=page_count)
                return True

            elif mime_type.startswith("image/"):
                from PIL import Image

                with Image.open(file_path) as img:
                    img.verify()

                # Re-open to get dimensions after verify
                with Image.open(file_path) as img:
                    width, height = img.size
                    if width == 0 or height == 0:
                        raise FileIntakeError("Image has invalid dimensions")

                logger.info("Image validated", width=width, height=height)
                return True

            return True
        except Exception as e:
            logger.error("Malformed file detection failed", error=str(e))
            raise FileIntakeError(f"File appears to be malformed: {e}") from e
