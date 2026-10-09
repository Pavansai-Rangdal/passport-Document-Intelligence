# Passport Document Intelligence — COMMANDS (without-laya-model branch)

> **Branch:** `without-laya-model`
> **Decision mode:** Fully deterministic — validation rules → policy engine → decision. No external ML model.
> **What's here:** Fastest possible decision path. Expiry date, MRZ validity, image quality, and field consistency checks are all handled locally with zero network dependency.

---

## Branch Overview

```
without-laya-model
  ├── Deterministic validation rules (always active)
  │     ├── Expiry date check (compared against today's date)
  │     ├── MRZ checksum validation
  │     ├── Image quality check (blur, brightness, dimensions)
  │     ├── Schema / field format validation
  │     └── VIZ ↔ MRZ consistency
  ├── Policy engine → final outcome (no external calls)
  ├── Evidence ledger records validation + policy evidence
  ├── Audit logging on every upload / extract / decision
  ├── Celery beat: daily retention cleanup
  └── GET /api/v1/batches/{id}/report endpoint
```

Other branches:
- `master` — System One optional (disabled by default)
- `with-laya-model` — System One enabled and fully wired

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | https://python.org |
| uv | latest | `pip install uv` |
| Docker Desktop | latest | https://docker.com/products/docker-desktop |
| Tesseract OCR | 5+ | See [OCR Setup](#ocr-setup) |

No external API credentials needed.

---

## 1. Clone & Install

```bash
git clone git@github.com:Pavansai-Rangdal/passport-Document-Intelligence.git
cd passport-Document-Intelligence
git checkout without-laya-model

uv sync
```

---

## 2. Environment Configuration

```bash
cp .env.example .env
```

Required changes in `.env`:

```env
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-random-32-char-secret
ENCRYPTION_KEY=your-random-32-char-key

# Database & Redis — defaults work with Docker below
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/passport_db
REDIS_URL=redis://localhost:6379/0

# OCR engine
OCR_ENGINE=tesseract   # or "paddle" or "both"
```

No System One variables needed on this branch — they have been removed from the codebase.

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

Verify:
```bash
docker ps
```

---

## 4. Run Database Migrations

```bash
uv run alembic upgrade head
```

### Migrating from master or with-laya-model?

If you previously ran migrations on `master` or `with-laya-model`, the
`decision_records` table has two extra columns (`system_one_recommendation`,
`system_one_confidence`) that no longer exist in this branch's model.
Drop them with:

```bash
# Generate and apply the drop-columns migration
uv run alembic revision --autogenerate -m "drop system_one columns"
uv run alembic upgrade head
```

Fresh install (no prior database): just run `uv run alembic upgrade head` as normal.

---

## 5. Start the API Server

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 6. Start Celery Worker + Beat

```bash
# Terminal 1 — processes tasks
uv run celery -A app.workers worker --loglevel=info

# Terminal 2 — daily retention scheduler
uv run celery -A app.workers beat --loglevel=info
```

---

## OCR Setup

### Tesseract

**Windows:** Download from https://github.com/UB-Mannheim/tesseract/wiki — add to system PATH.

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

### Make Decision (deterministic, instant)
```bash
curl -X POST http://localhost:8000/api/v1/documents/{document_id}/decide
```

Response on this branch — no System One fields:
```json
{
  "decision_id": "uuid",
  "outcome": "pass_screening",
  "confidence": 0.87,
  "reasoning": "Document passed all validation rules",
  "policy_version": "1.0",
  "triggered_rules": [],
  "validation_summary": {}
}
```

`confidence` is calculated as the fraction of validation rules that passed.

### Batch Operations
```bash
curl -X POST http://localhost:8000/api/v1/batches
curl http://localhost:8000/api/v1/batches/{batch_id}
curl http://localhost:8000/api/v1/batches/{batch_id}/report
```

---

## How Decisions Are Made (No ML)

The policy engine applies these rules **in order**, stopping at the first match:

| Priority | Rule | Outcome |
|----------|------|---------|
| 1 | Critical validation error (e.g. passport expired, bad checksum) | `FAIL_RULE` |
| 2 | Validation warnings (e.g. low image quality) | `REVIEW_REQUIRED` |
| 3 | MRZ not detected | `INSUFFICIENT_DATA` |
| 4 | All validations passed | `PASS_SCREENING` |

The expiry date check runs as part of step 1 — if `expiry_date` from OCR is in the past,
it triggers a critical error and the document immediately gets `FAIL_RULE`.

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

# Generate a new migration after model changes
uv run alembic revision --autogenerate -m "description"
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
| `PASS_SCREENING` | All validation rules passed |
| `FAIL_RULE` | Critical error (expired passport, bad MRZ checksum, etc.) |
| `REVIEW_REQUIRED` | Warnings (image quality, minor inconsistencies) |
| `INSUFFICIENT_DATA` | MRZ not detected in image |

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
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | `json` | `json` or `text` |

---

## Troubleshooting

### `password authentication failed`
Check `DATABASE_URL` in `.env` matches your Docker credentials.

### `No OCR engine available`
Run `tesseract --version`. On Windows, verify Tesseract is on system PATH.

### `connection refused` on 5432 or 6379
```bash
docker start passport_db passport_redis
```

### Import errors
```bash
uv sync
find . -type d -name __pycache__ -exec rm -rf {} +
```

### Alembic `column does not exist` error
You have leftover `system_one_*` columns from a prior branch. Run:
```bash
uv run alembic revision --autogenerate -m "drop system_one columns"
uv run alembic upgrade head
```

### Celery beat not running retention
Ensure both `celery worker` and `celery beat` are running.
Check Redis: `redis-cli ping`
