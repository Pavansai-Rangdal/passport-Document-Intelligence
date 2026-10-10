"""Passport expiry classification endpoint (with Laya model)."""

import tempfile
from datetime import date
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.core.exceptions import ExtractionError
from app.core.logging import get_logger
from app.extraction import ExtractionService
from app.laya import LayaClient
from app.schemas.classify import ClassificationResponse

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()

_extraction_service = ExtractionService()

_ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "application/pdf"}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


def _laya_client() -> LayaClient | None:
    """Return a LayaClient if the API URL is configured, else None."""
    if settings.laya_api_url:
        return LayaClient(
            api_url=settings.laya_api_url,
            api_key=settings.laya_api_key,
            timeout=settings.laya_timeout_seconds,
        )
    return None


@router.post("/classify", response_model=ClassificationResponse)
async def classify_passport(file: UploadFile = File(...)):
    """Upload a passport image. Returns whether the passport is expired.

    Classification strategy:
    1. If Laya API is configured, send the image to the Laya model first.
    2. If Laya is unavailable or not configured, fall back to MRZ extraction.
    """
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    contents = await file.read()
    if len(contents) > _MAX_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 10 MB limit")

    suffix = Path(file.filename or "upload.jpg").suffix or ".jpg"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        # ── Attempt Laya model classification ───────────────────────────────
        client = _laya_client()
        if client is not None:
            try:
                laya_result = client.classify(tmp_path)
                expired = laya_result.get("expired")
                expiry_raw = laya_result.get("expiry_date")
                confidence = float(laya_result.get("confidence", 0.0))

                if expired is None:
                    message = "Laya model could not determine expiry"
                elif expired:
                    message = f"Passport expired on {expiry_raw}" if expiry_raw else "Passport is expired"
                else:
                    message = f"Passport is valid until {expiry_raw}" if expiry_raw else "Passport is valid"

                return ClassificationResponse(
                    expired=expired,
                    expiry_date=expiry_raw,
                    confidence=confidence,
                    mrz_detected=False,
                    method="laya_model",
                    message=message,
                )
            except Exception as laya_err:
                logger.warning("Laya model failed, falling back to MRZ extraction", error=str(laya_err))

        # ── Fallback: MRZ extraction ─────────────────────────────────────────
        try:
            extraction = _extraction_service.extract_from_image(tmp_path)
        except ExtractionError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.error("Extraction failed unexpectedly", error=str(e))
            raise HTTPException(status_code=500, detail="Extraction failed")

        mrz_data = extraction.get("mrz_data") or {}
        expiry_raw = mrz_data.get("expiry_date_normalized") or mrz_data.get("expiry_date")
        mrz_detected = extraction.get("mrz_detected", False)

        expired: bool | None = None
        if expiry_raw:
            try:
                expired = date.fromisoformat(expiry_raw) < date.today()
            except ValueError:
                pass

        confidence = 0.9 if mrz_detected else 0.3

        if expired is None:
            message = "Could not determine expiry — MRZ not detected or expiry date unreadable"
        elif expired:
            message = f"Passport expired on {expiry_raw}"
        else:
            message = f"Passport is valid until {expiry_raw}"

        return ClassificationResponse(
            expired=expired,
            expiry_date=expiry_raw,
            confidence=confidence,
            mrz_detected=mrz_detected,
            method="mrz_extraction_fallback",
            message=message,
        )

    finally:
        tmp_path.unlink(missing_ok=True)
