"""Passport expiry classification endpoint."""

import tempfile
from datetime import date
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.core.exceptions import ExtractionError
from app.core.logging import get_logger
from app.extraction import ExtractionService
from app.schemas.classify import ClassificationResponse

router = APIRouter()
logger = get_logger(__name__)

_extraction_service = ExtractionService()

_settings = get_settings()
_ALLOWED_TYPES = set(_settings.allowed_upload_types)
_ALLOWED_EXTENSIONS = {e.strip().lower() for e in _settings.allowed_upload_extensions.split(",")}
_MAX_BYTES = _settings.max_upload_mb * 1024 * 1024

# Confidence bands: (floor, span) — confidence = floor + check_digit_score * span
_CONF_EXPIRY_KNOWN = (0.50, 0.45)  # 0.50 (all checks fail) → 0.95 (all pass)
_CONF_EXPIRY_UNREADABLE = (0.20, 0.25)  # MRZ found, expiry unreadable
_CONF_NO_MRZ = 0.10
_CONF_ERROR = 0.0
_DEFAULT_CHECK_SCORE = 0.5
_METHOD_MRZ = "mrz_extraction"
_METHOD_ERROR = "error"
_METHOD_LAYA = "laya_model"
_METHOD_MRZ_FALLBACK = "mrz_extraction_fallback"

_laya_classifier = None


def _get_laya_classifier():
    """Lazily initialise the Laya classifier on first use (None when not configured)."""
    global _laya_classifier
    if _laya_classifier is None and _settings.laya_checkpoint_path:
        from app.laya import LayaClassifier

        _laya_classifier = LayaClassifier(_settings.laya_checkpoint_path)
    return _laya_classifier


async def process_single_file(file: UploadFile) -> ClassificationResponse:
    """Process a single passport file and return classification result."""
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    if Path(file.filename or "").suffix.lower() not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {file.filename}")

    contents = await file.read()
    if len(contents) > _MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"File exceeds {_settings.max_upload_mb} MB limit")

    suffix = Path(file.filename or "upload.jpg").suffix or ".jpg"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        extraction = await run_in_threadpool(_extraction_service.extract_from_image, tmp_path)
    except ExtractionError:
        # OCR couldn't extract text — return unknown result rather than error
        extraction = {"mrz_detected": False, "mrz_data": None}
    except Exception as e:
        logger.error("Extraction failed unexpectedly", error=str(e))
        raise HTTPException(status_code=500, detail="Extraction failed")
    finally:
        tmp_path.unlink(missing_ok=True)

    mrz_data = extraction.get("mrz_data") or {}
    expiry_raw = mrz_data.get("expiry_date_normalized") or mrz_data.get("expiry_date")
    mrz_detected = extraction.get("mrz_detected", False)
    check_score: float | None = mrz_data.get("check_digit_score")  # 0.0–1.0 or None

    expired: bool | None = None
    if expiry_raw:
        try:
            expired = date.fromisoformat(expiry_raw) < date.today()
        except ValueError:
            pass

    if expired is not None:
        score = check_score if check_score is not None else _DEFAULT_CHECK_SCORE
        confidence = round(_CONF_EXPIRY_KNOWN[0] + score * _CONF_EXPIRY_KNOWN[1], 2)
    elif mrz_detected:
        score = check_score if check_score is not None else _DEFAULT_CHECK_SCORE
        confidence = round(_CONF_EXPIRY_UNREADABLE[0] + score * _CONF_EXPIRY_UNREADABLE[1], 2)
    else:
        confidence = _CONF_NO_MRZ

    if expired is None:
        message = "Could not determine expiry — MRZ not detected or expiry date unreadable"
    elif expired:
        message = f"Passport expired on {expiry_raw}"
    else:
        message = f"Passport is valid until {expiry_raw}"

    method = _METHOD_MRZ

    # If LAYA_CHECKPOINT_PATH is set, Laya makes the expiry decision from the extracted
    # data; on any failure the deterministic MRZ date comparison above is kept.
    try:
        laya = await run_in_threadpool(_get_laya_classifier)
        if laya is not None:
            method = _METHOD_MRZ_FALLBACK
            laya_result = await run_in_threadpool(laya.classify, extraction)
            expired, confidence = laya_result["expired"], laya_result["confidence"]
            method = _METHOD_LAYA
            if expired is None:
                message = "Laya model could not determine expiry"
            elif expired:
                message = f"Passport expired on {expiry_raw}" if expiry_raw else "Passport is expired"
            else:
                message = f"Passport is valid until {expiry_raw}" if expiry_raw else "Passport is valid"
    except Exception as laya_err:
        logger.warning("Laya classification failed, using MRZ date check", error=str(laya_err))

    return ClassificationResponse(
        expired=expired,
        expiry_date=expiry_raw,
        confidence=confidence,
        mrz_detected=mrz_detected,
        method=method,
        message=message,
        filename=file.filename,
    )


def _error_response(file: UploadFile, message: str) -> ClassificationResponse:
    return ClassificationResponse(
        expired=None,
        expiry_date=None,
        confidence=_CONF_ERROR,
        mrz_detected=False,
        method=_METHOD_ERROR,
        message=message,
        filename=file.filename,
    )


async def _classify_safely(file: UploadFile) -> ClassificationResponse:
    """Classify one file; any failure becomes an error result so a batch never aborts."""
    try:
        return await process_single_file(file)
    except HTTPException as e:
        logger.error(f"Failed to process file {file.filename}: {e.detail}")
        return _error_response(file, f"Error processing {file.filename}: {e.detail}")
    except Exception as e:
        logger.error(f"Unexpected error processing file {file.filename}: {str(e)}")
        return _error_response(file, f"Unexpected error processing {file.filename}")


@router.post("/classify", response_model=List[ClassificationResponse])
async def classify_passport(files: List[UploadFile] = File(...)):
    """Upload passport images or PDFs. Returns whether each passport is expired."""
    return [await _classify_safely(file) for file in files]


@router.post("/classify/stream")
async def classify_passport_stream(files: List[UploadFile] = File(...)):
    """Same as /classify, but streams one JSON result per line (NDJSON) as each file finishes."""

    async def generate():
        for file in files:
            result = await _classify_safely(file)
            yield result.model_dump_json() + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")
