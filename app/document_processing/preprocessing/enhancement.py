"""Image enhancement for better OCR results."""

from pathlib import Path

import cv2
import numpy as np

from app.core.logging import get_logger

logger = get_logger(__name__)


class ImageEnhancer:
    """Enhances images for better OCR accuracy."""

    @staticmethod
    def denoise(image: np.ndarray) -> np.ndarray:
        """Apply denoising to image."""
        try:
            denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
            logger.info("Image denoised")
            return denoised
        except Exception as e:
            logger.error("Failed to denoise image", error=str(e))
            return image

    @staticmethod
    def enhance_contrast(image: np.ndarray) -> np.ndarray:
        """Enhance image contrast using CLAHE."""
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel, a, b = cv2.split(lab)

            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_channel = clahe.apply(l_channel)

            # Merge channels and convert back
            enhanced = cv2.merge([l_channel, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

            logger.info("Image contrast enhanced")
            return enhanced
        except Exception as e:
            logger.error("Failed to enhance contrast", error=str(e))
            return image

    @staticmethod
    def sharpen(image: np.ndarray) -> np.ndarray:
        """Apply sharpening filter."""
        try:
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(image, -1, kernel)
            logger.info("Image sharpened")
            return sharpened
        except Exception as e:
            logger.error("Failed to sharpen image", error=str(e))
            return image

    @staticmethod
    def binarize(image: np.ndarray) -> np.ndarray:
        """Convert image to binary using adaptive thresholding."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            logger.info("Image binarized")
            return binary
        except Exception as e:
            logger.error("Failed to binarize image", error=str(e))
            return image

    @staticmethod
    def enhance_image(image_path: Path, output_path: Path) -> bool:
        """Apply full enhancement pipeline."""
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError("Failed to load image")

            # Apply enhancements
            enhanced = ImageEnhancer.denoise(image)
            enhanced = ImageEnhancer.enhance_contrast(enhanced)
            enhanced = ImageEnhancer.sharpen(enhanced)

            # Save enhanced image
            cv2.imwrite(str(output_path), enhanced)

            logger.info("Image enhancement completed", output_path=str(output_path))
            return True
        except Exception as e:
            logger.error("Image enhancement failed", error=str(e))
            return False
