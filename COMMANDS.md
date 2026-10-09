# Passport Document Intelligence — COMMANDS (master branch)

> **Branch:** `master`
> **Decision mode:** Deterministic rules + optional System One ML model (disabled by default)
> **What's here:** Full pipeline with audit logging, evidence ledger, batch reporting, daily retention cleanup via Celery beat. System One is wired but off — enable it via env vars when you have credentials.

---

## Branch Overview

```
master
  ├── Deterministic policy engine (always active)
  ├── System One ML model (optional — set SYSTEM_ONE_ENABLED=true to activate)
  ├── Audit logging on every upload / extract / decision
  ├── Evidence ledger persists validation + policy evidence
  ├── Celery beat: daily retention cleanup
  └── GET /api/v1/batches/{id}/report endpoint
```

Other branches:
- `with-laya-model` — System One enabled and fully configured by default
- `without-laya-model` — System One removed entirely; pure deterministic pipeline

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | https://python.org |
| uv | latest | `pip install uv` |
| Docker Desktop | latest | https://docker.com/products/docker-desktop |
| Tesseract OCR | 5+ | See [OCR Setup](#ocr-setup) |

---

## 1. Clone & Install

```bash
git clone git@github.com:Pavansai-Rangdal/passport-Document-Intelligence.git
cd passport-Document-Intelligence
git checkout master

uv sync
```

---

## 2. Environment Configuration

```bash
cp .env.example .env
```

Minimum required changes in `.env`:

```env
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-random-32-char-secret
ENCRYPTION_KEY=your-random-32-char-key

# Database & Redis — defaults work with Docker below
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/passport_db
REDIS_URL=redis://localhost:6379/0

# OCR engine
OCR_ENGINE=tesseract   # or "paddle" or "both"

# System One — leave disabled unless you have credentials
SYSTEM_ONE_ENABLED=false
SYSTEM_ONE_API_URL=
SYSTEM_ONE_API_KEY=
```

To enable System One when credentials are available:
```env
SYSTEM_ONE_ENABLED=true
SYSTEM_ONE_API_URL=https://api.your-system-one-endpoint.com
SYSTEM_ONE_API_KEY=your-api-key
SYSTEM_ONE_TIMEOUT_SECONDS=30
```

---

## 3. Start Infrastructure

```bash
# PostgreSQL
docker run -d --name passport_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=passport_db \
  -p 5432:5432 \
  postgres:16-alpine

# Redis (required for Celery beat retention cleanup)
docker run -d --name passport_redis \
  -p 6379:6379 \
  redis:7-alpine
```

Verify both running:
```bash
docker ps
```

---

## 4. Run Database Migrations

```bash
uv run alembic upgrade head
```

---

## 5. Start the API Server

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 6. Start Celery Worker + Beat (Retention Cleanup)

Run in a separate terminal. Both worker and beat are needed for the daily retention task:

```bash
# Worker (processes tasks)
uv run celery -A app.workers worker --loglevel=info

# Beat scheduler (triggers daily retention — separate terminal)
uv run celery -A app.workers beat --loglevel=info
```

---

## OCR Setup

### Tesseract

**Windows:** Download from https://github.com/UB-Mannheim/tesseract/wiki — add install dir to system PATH.

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

Verify:
```bash
tesseract --version
```

### PaddleOCR (optional)

```bash
uv sync --extra ocr-paddle
```

---

## API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/path/to/passport.jpg"
```

### Extract Data
```bash
curl -X POST http://localhost:8000/api/v1/documents/{document_id}/extract
```

### Make Decision
```bash
# If SYSTEM_ONE_ENABLED=false → deterministic rules only
# If SYSTEM_ONE_ENABLED=true  → validation + System One + policy engine
curl -X POST http://localhost:8000/api/v1/documents/{document_id}/decide
```

Decision response includes `system_one_recommendation` and `system_one_confidence` fields
(both `null` when System One is disabled).

### Batch Operations
```bash
curl -X POST http://localhost:8000/api/v1/batches
curl http://localhost:8000/api/v1/batches/{batch_id}
curl http://localhost:8000/api/v1/batches/{batch_id}/report
```

---

## Testing

```bash
uv run pytest
uv run pytest -v
uv run pytest --cov=app --cov-report=html
uv run pytest tests/test_validation_rules.py -v
```

---

## Code Quality

```bash
uv run ruff check app/
uv run ruff check app/ --fix
uv run ruff format app/
uv run mypy app/
```

---

## Database Migrations

```bash
uv run alembic upgrade head        # Apply all pending migrations
uv run alembic downgrade -1        # Roll back one
uv run alembic downgrade base      # Roll back everything
uv run alembic current             # Show current state
```

---

## Docker Compose (Full Stack)

```bash
docker-compose up -d
docker-compose exec web uv run alembic upgrade head
docker-compose logs -f
docker-compose down
```

---

## Decision Outcomes

| Outcome | Trigger |
|---------|---------|
| `PASS_SCREENING` | All validations passed (+ System One pass if enabled) |
| `FAIL_RULE` | Critical validation error, or System One high-confidence fail |
| `REVIEW_REQUIRED` | Warnings, or System One recommends review / low confidence |
| `INSUFFICIENT_DATA` | MRZ not detected |

---

## Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/passport_db` | PostgreSQL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `OCR_ENGINE` | `both` | `tesseract`, `paddle`, or `both` |
| `SECRET_KEY` | *(change this)* | Signing key |
| `ENCRYPTION_KEY` | *(change this)* | Field encryption key |
| `STORAGE_PATH` | `data/uploads` | Upload storage |
| `STORAGE_MAX_FILE_SIZE` | `10485760` | Max upload (10 MB) |
| `RETENTION_DAYS` | `90` | Days before files are purged |
| `SYSTEM_ONE_ENABLED` | `false` | Enable System One ML model |
| `SYSTEM_ONE_API_URL` | *(empty)* | System One API endpoint |
| `SYSTEM_ONE_API_KEY` | *(empty)* | System One API key |
| `SYSTEM_ONE_TIMEOUT_SECONDS` | `30` | System One request timeout |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | `json` | `json` or `text` |

---

## Troubleshooting

### `password authentication failed`
Check `DATABASE_URL` in `.env` matches your Docker container credentials.

### `No OCR engine available`
Tesseract not installed or not on PATH. Run `tesseract --version` to verify.

### `connection refused` on 5432 or 6379
```bash
docker start passport_db passport_redis
```

### Import errors
```bash
uv sync
find . -type d -name __pycache__ -exec rm -rf {} +
```

### Celery beat not running retention
Ensure `celery beat` process is running alongside `celery worker`.
Check Redis is reachable: `redis-cli ping`
