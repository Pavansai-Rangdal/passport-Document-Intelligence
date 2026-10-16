# Passport Expiry Checker

A web application that reads the Machine Readable Zone (MRZ) of passport images and reports whether each passport is **expired**, **valid**, or **unknown**. Upload one or many files and watch results appear as each file finishes processing.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
  - [System Context](#system-context)
  - [Processing Pipeline](#processing-pipeline)
  - [Backend Modules](#backend-modules)
  - [OCR Strategy](#ocr-strategy)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running Locally](#running-locally)
  - [Docker](#docker)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Confidence Scoring](#confidence-scoring)
- [Development](#development)
- [Known Limitations](#known-limitations)

## Overview

Passport expiry is encoded in the two-line (TD3) or three-line (TD1) MRZ printed on identity documents, following ICAO Doc 9303. This service locates the MRZ, extracts it with OCR, validates it using the ICAO check digits, and compares the expiry date with today's date.

Processing is deterministic: no machine-learning classifier decides the outcome. OCR produces text, and a rule-based parser and date comparison produce the verdict.

## Features

- Batch upload of multiple images in a single request
- Streamed results: each file's verdict is shown as soon as it is ready
- Dual OCR engines with automatic fallback (PaddleOCR primary, EasyOCR secondary)
- ICAO 9303 MRZ parsing for TD1, TD2 and TD3 formats
- Check-digit validation that drives a per-file confidence score
- Per-file error isolation: one bad file never fails the batch
- Upload limits, accepted file types and timeouts configured through `.env`
- Structured JSON logging

## Architecture

### System Context

```
┌──────────────────────┐   /api, /health    ┌──────────────────────────────┐
│  React SPA           │ ─────────────────▶ │  FastAPI backend             │
│  (Vite dev server    │   multipart upload │                              │
│   or static build)   │ ◀───────────────── │  POST /api/v1/classify       │
│                      │   NDJSON stream    │  POST /api/v1/classify/stream│
└──────────────────────┘                    │  GET  /health                │
                                            └──────────────┬───────────────┘
                                                           │
                                            ┌──────────────▼───────────────┐
                                            │  Extraction service          │
                                            │  PaddleOCR ─▶ EasyOCR (fallback)
                                            └──────────────────────────────┘
```

During development the Vite dev server proxies `/api` and `/health` to the backend, so the browser only ever talks to one origin.

### Processing Pipeline

Each uploaded file passes through the same stages:

```
Upload ─▶ Validate ─▶ Quality check ─▶ MRZ zone detection ─▶ OCR
                                                                │
Verdict ◀─ Confidence ◀─ Expiry vs. today ◀─ MRZ parse ◀────────┘
                                          (check digits, date normalization)
```

1. **Validate**: content type, file extension and size are checked against configured limits.
2. **Quality check**: resolution, blur and brightness are measured for diagnostics.
3. **MRZ detection**: OpenCV locates the MRZ region.
4. **OCR**: the bottom of the page (the MRZ zone) and the full page are read.
5. **Parse**: MRZ lines are extracted from the OCR text and parsed by document type (TD1, TD2 or TD3).
6. **Decide**: the expiry date is normalized and compared with the current date, and a confidence score is derived from the check digits.

### Backend Modules

| Module | Responsibility |
| --- | --- |
| `app/api` | FastAPI routers: classification (batch and streaming) and health |
| `app/core` | Settings, structured logging, exceptions |
| `app/document_processing` | Image loading, quality assessment, enhancement, MRZ and document detection, PDF renderer |
| `app/extraction` | Extraction service, OCR engines, MRZ parser and check digits, field and date normalization |
| `app/schemas` | Pydantic request and response models |

### OCR Strategy

- **PaddleOCR** runs first. It reads the bottom 28% of the image, where the MRZ sits, and then the full page.
- **EasyOCR** performs the same two passes, but only when PaddleOCR returns no text or its text yields no parsable MRZ. Its MRZ pass is restricted to the characters `A-Z`, `0-9` and `<`.
- OCR runs in a worker thread, so a slow file does not block the server while earlier results are being streamed.

## Tech Stack

| Layer | Technology | Version |
| --- | --- | --- |
| Language | Python | 3.11+ (developed on 3.12) |
| Web framework | FastAPI, Uvicorn | 0.115+ |
| Validation and settings | Pydantic, pydantic-settings | 2.x |
| Primary OCR | PaddleOCR, PaddlePaddle (CPU), PaddleX | 3.7.0, 3.3.1, 3.7.2 |
| Fallback OCR | EasyOCR on PyTorch | 1.7.2 |
| OCR models | PP-OCRv6 medium (detection and recognition), CRAFT, English g2 | n/a |
| Image processing | OpenCV (headless), Pillow, NumPy, scikit-image | 4.x, 12.x, 2.x, 0.26 |
| PDF rendering | PyMuPDF | 1.25+ |
| Logging | structlog | 25.x |
| Frontend | React, React Router, Axios | 18, 6, 1.x |
| Frontend tooling | Vite, Tailwind CSS, PostCSS | 5, 3, 8 |
| Packaging | uv, Hatchling | n/a |
| Tooling | Ruff, mypy, pytest | n/a |
| Container | Docker | n/a |

## Project Structure

```
.
├── app/
│   ├── api/routes/            # classify.py, health.py
│   ├── core/                  # config.py, logging.py, exceptions.py
│   ├── document_processing/   # detection/, preprocessing/, pdf_renderer.py
│   ├── extraction/            # extraction_service.py, ocr/, mrz/, normalization/
│   ├── schemas/               # classify.py, common.py
│   └── main.py                # FastAPI entry point
├── frontend/
│   ├── src/
│   │   ├── api/client.js      # classify and streaming clients
│   │   ├── pages/Classifier.jsx
│   │   ├── config.js          # values injected from .env
│   │   └── App.jsx
│   └── vite.config.js
├── docker/Dockerfile
├── scripts/test_extraction.py # run extraction over a folder of samples
├── .env.example
└── pyproject.toml
```

## Getting Started

### Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- Node.js 18 or newer
- About 300 MB of disk for OCR models, which download on first use

### Installation

```bash
# Backend
uv sync

# Frontend
cd frontend
npm install
```

Create your environment file from the template:

```bash
cp .env.example .env
```

### Running Locally

Start the backend (port `8888` by default):

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8888
```

Start the frontend in a second terminal:

```bash
cd frontend
npm run dev
```

| Service | URL |
| --- | --- |
| Web app | http://localhost:3000 |
| API | http://localhost:8888 |
| Interactive API docs | http://localhost:8888/docs |

The first request is slow because the OCR models are loaded and, on a fresh machine, downloaded.

### Docker

```bash
docker build -f docker/Dockerfile -t passport-expiry-checker .
docker run -p 8888:8888 passport-expiry-checker
```

The image contains the backend only. `.env` is not copied into the image, so pass settings with `-e` flags or `--env-file`.

## Configuration

All settings are read from `.env`. The frontend build reads the upload settings from the same file.

| Variable | Default | Description |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Backend bind address |
| `PORT` | `8888` | Backend port, also used by the dev proxy |
| `FRONTEND_PORT` | `3000` | Vite dev server port |
| `MAX_UPLOAD_MB` | `10` | Maximum size of each uploaded file |
| `ALLOWED_UPLOAD_EXTENSIONS` | `.jpg,.jpeg,.png,.webp,.pdf` | Accepted extensions, shared by backend and frontend |
| `REQUEST_TIMEOUT_MS` | `600000` | Frontend request timeout |
| `OCR_ENGINE` | `paddle` | Reserved. Engine order is currently fixed in code (PaddleOCR, then EasyOCR) |
| `OCR_CONFIDENCE_THRESHOLD` | `0.7` | Reserved. Not used by the pipeline yet |
| `MIN_IMAGE_WIDTH`, `MIN_IMAGE_HEIGHT` | `800`, `600` | Image quality thresholds |
| `MAX_BLUR_SCORE` | `100.0` | Maximum blur score |
| `MIN_BRIGHTNESS`, `MAX_BRIGHTNESS` | `50.0`, `200.0` | Brightness bounds |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING` or `ERROR` |
| `LOG_FORMAT` | `json` | `json` or `text` |

## API Reference

### `GET /health`

Returns service status.

```json
{ "status": "healthy", "version": "0.1.0", "environment": "development" }
```

### `POST /api/v1/classify`

Accepts one or more files in the multipart field `files` and returns a JSON array with one result per file.

```bash
curl -X POST http://localhost:8888/api/v1/classify \
  -F "files=@passport-1.jpg" \
  -F "files=@passport-2.png"
```

### `POST /api/v1/classify/stream`

Same input as `/classify`. The response is `application/x-ndjson`: one JSON result per line, sent as each file completes, in upload order.

### Result object

```json
{
  "expired": false,
  "expiry_date": "2034-02-08",
  "confidence": 0.95,
  "mrz_detected": true,
  "method": "mrz_extraction",
  "message": "Passport is valid until 2034-02-08",
  "filename": "passport-1.jpg"
}
```

| Field | Description |
| --- | --- |
| `expired` | `true`, `false`, or `null` when the expiry could not be determined |
| `expiry_date` | ISO date (`YYYY-MM-DD`) or `null` |
| `confidence` | Value between 0 and 1, see below |
| `mrz_detected` | Whether an MRZ was found and parsed |
| `method` | `mrz_extraction`, or `error` when the file could not be processed |
| `message` | Human-readable summary |
| `filename` | Name of the uploaded file |

Files with an unsupported type or extension, or over the size limit, return a result with `method: "error"` and an explanatory `message`. They do not fail the request.

## Confidence Scoring

Confidence is derived from the ICAO check digits for the document number, date of birth and expiry date.

| Situation | Confidence |
| --- | --- |
| Expiry read, all check digits pass | 0.95 |
| Expiry read, all check digits fail | 0.50 |
| MRZ found but expiry unreadable | 0.20 to 0.45 |
| No MRZ detected | 0.10 |
| File could not be processed | 0.00 |

## Development

```bash
# Lint and format
uv run ruff check app/
uv run ruff format app/

# Run extraction over a folder of sample images
uv run python scripts/test_extraction.py

# Frontend production build
cd frontend
npm run build
```

Notes for working on OCR:

- PaddleOCR is created with `enable_mkldnn=False`. oneDNN in PaddlePaddle 3.3.x raises a runtime error on some CPU builds.
- PaddleOCR 3.x returns dict-like result objects. Read them with the `_page_field` helper in `app/extraction/ocr/paddle_ocr.py`.
- On Windows, run with `PYTHONUTF8=1` when scripts print OCR text, to avoid console encoding errors.

## Known Limitations

- PDF uploads are accepted, but the PDF renderer is not yet connected to the extraction step, so PDFs are not read.
- OCR runs on CPU. Large images can take around a minute each; the streamed output keeps the interface responsive.
- Only passports with a readable MRZ can be classified. Documents without one return `unknown`.
- The project has no automated test suite yet.
