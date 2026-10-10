"""Laya (System One) ML model client for passport expiry classification."""

from pathlib import Path
from typing import Any

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)


class LayaClient:
    """HTTP client for the Laya (System One) passport classification model.

    The model accepts a passport image and returns a classification:
    expired / valid / unknown, along with a confidence score.

    Expected response JSON:
    {
        "expired": true | false | null,
        "expiry_date": "YYYY-MM-DD" | null,
        "confidence": 0.0 - 1.0,
        "model_version": "..."
    }
    """

    def __init__(self, api_url: str, api_key: str, timeout: int = 30) -> None:
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    def classify(self, image_path: Path) -> dict[str, Any]:
        """Send image to Laya model and return classification result.

        Returns a dict with keys:
            expired (bool | None), expiry_date (str | None),
            confidence (float), model_version (str)

        Raises:
            httpx.HTTPError: on network or HTTP-level errors.
        """
        logger.info("Sending image to Laya model", path=str(image_path))

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        suffix = image_path.suffix.lower()
        mime = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
        }.get(suffix, "application/octet-stream")

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self._api_url}/classify",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Accept": "application/json",
                },
                files={"file": (image_path.name, image_bytes, mime)},
            )
            response.raise_for_status()

        result = response.json()
        logger.info(
            "Laya model responded",
            expired=result.get("expired"),
            confidence=result.get("confidence"),
        )
        return result
