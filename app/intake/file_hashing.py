"""File hashing utilities for deduplication and integrity."""

import hashlib
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute hash of a file."""
    hasher = hashlib.new(algorithm)

    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)

        file_hash = hasher.hexdigest()
        logger.info("File hash computed", algorithm=algorithm, file_path=str(file_path))
        return file_hash
    except Exception as e:
        logger.error("Failed to compute file hash", error=str(e))
        raise
