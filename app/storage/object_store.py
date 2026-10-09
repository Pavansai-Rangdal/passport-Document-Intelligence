"""Object store for file storage management."""

from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()


class ObjectStore:
    """Manages file storage."""

    def __init__(self) -> None:
        self.storage_path = settings.storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def get_storage_path(self) -> Path:
        """Get the storage path."""
        return self.storage_path

    def store_file(self, content: bytes, filename: str) -> Path:
        """Store a file in the object store."""
        import uuid

        file_extension = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.storage_path / unique_filename

        file_path.write_bytes(content)

        logger.info("File stored", file_path=str(file_path), size=len(content))
        return file_path

    def get_file(self, file_path: str) -> bytes:
        """Get file content."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = path.read_bytes()
        logger.info("File retrieved", file_path=file_path, size=len(content))
        return content

    def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        path = Path(file_path)
        if not path.exists():
            logger.warning("File not found for deletion", file_path=file_path)
            return False

        path.unlink()
        logger.info("File deleted", file_path=file_path)
        return True

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        return Path(file_path).exists()
