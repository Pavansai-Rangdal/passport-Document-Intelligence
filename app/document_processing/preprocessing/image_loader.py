"""Image loading utilities."""

from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image

from app.core.logging import get_logger

logger = get_logger(__name__)


class ImageLoader:
    """Loads images from various formats."""

    @staticmethod
    def load_image(file_path: Path) -> np.ndarray:
        """Load image as numpy array using OpenCV."""
        try:
            image = cv2.imread(str(file_path))
            if image is None:
                raise ValueError(f"Failed to load image: {file_path}")
            logger.info("Image loaded", file_path=str(file_path), shape=image.shape)
            return image
        except Exception as e:
            logger.error("Failed to load image", error=str(e))
            raise

    @staticmethod
    def load_image_pil(file_path: Path) -> Image.Image:
        """Load image using PIL."""
        try:
            image = Image.open(file_path)
            logger.info("Image loaded with PIL", file_path=str(file_path), size=image.size)
            return image
        except Exception as e:
            logger.error("Failed to load image with PIL", error=str(e))
            raise

    @staticmethod
    def get_image_info(file_path: Path) -> dict[str, Any]:
        """Get basic image information."""
        try:
            image = Image.open(file_path)
            width, height = image.size
            dpi = image.info.get("dpi", (72, 72))[0] if "dpi" in image.info else 72

            return {
                "width": width,
                "height": height,
                "dpi": dpi,
                "format": image.format,
                "mode": image.mode,
            }
        except Exception as e:
            logger.error("Failed to get image info", error=str(e))
            raise
