# Passport Document Intelligence — Quick Start Guide

Everything a new developer needs to get the project running from scratch.

---

## Prerequisites

Install these before anything else:

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | https://python.org |
| uv | latest | `pip install uv` or https://docs.astral.sh/uv |
| Docker Desktop | latest | https://docker.com/products/docker-desktop |
| Tesseract OCR | 5+ | See [OCR Setup](#ocr-setup) below |

---

## 1. Clone & Install

```bash
git clone <repository-url>
cd Passport-Document-Intelligence

# Install all Python dependencies
uv sync
```

---

## 2. Environment Configuration

```bash
# Copy the example env file
cp .env.example .env
```

Open `.env` and update at minimum these values:

```env
# Required — change these secrets before running
SECRET_KEY=your-random-32-char-secret-here
ENCRYPTION_KEY=your-random-32-char-key-here

# Database (defaults work if you use Docker below)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/passport_db

# Redis (defaults work if you use Docker below)
REDIS_URL=redis://localhost:6379/0

# OCR engine: "tesseract", "paddle", or "both"
OCR_ENGINE=tesseract
```

Generate secure keys with:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 3. Start Infrastructure (Docker)

Start PostgreSQL and Redis with a single command:

```bash
docker run -d --name passport_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=passport_db \
  -p 5432:5432 \
  postgres:16-alpine

docker run -d --name passport_redis \
  -p 6379:6379 \
  redis:7-alpine
```

Verify both are running:
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

The API is now available at:
- **API root**: http://localhost:8000
- **Swagger UI** (interactive docs): http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 6. OCR Setup

The system needs at least one OCR engine.

### Tesseract (recommended for development)

**Windows:** Download and install from https://github.com/UB-Mannheim/tesseract/wiki  
Then add the install directory (e.g. `C:\Program Files\Tesseract-OCR`) to your system PATH.

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

Verify installation:
```bash
tesseract --version
```

### PaddleOCR (optional, GPU-capable)

```bash
uv sync --extra ocr-paddle
```

---

## API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Upload a Passport Document
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@/path/to/passport.jpg"
```

Response includes `document_id` — use it in subsequent calls.

### Extract Data from Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/{document_id}/extract
```

### Make a Decision
```bash
curl -X POST http://localhost:8000/api/v1/documents/{document_id}/decide
```

### Create a Batch
```bash
curl -X POST http://localhost:8000/api/v1/batches
```

### Get Batch Status
```bash
curl http://localhost:8000/api/v1/batches/{batch_id}
```

---

## Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=app --cov-report=html

# Run a specific test file
uv run pytest tests/test_validation_rules.py -v
```

---

## Code Quality

```bash
# Lint
uv run ruff check app/

# Auto-fix lint errors
uv run ruff check app/ --fix

# Format code
uv run ruff format app/

# Type check
uv run mypy app/
```

---

## Background Worker (Celery)

If you need background task processing, start the Celery worker in a separate terminal:

```bash
uv run celery -A app.workers worker --loglevel=info
```

This requires Redis to be running.

---

## Full Docker Compose (Production-like)

If a `docker-compose.yml` is present:

```bash
# Start all services
docker-compose up -d

# Run migrations inside the container
docker-compose exec web uv run alembic upgrade head

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

---

## Database Migrations

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Roll back one migration
uv run alembic downgrade -1

# Roll back everything
uv run alembic downgrade base

# Check current migration state
uv run alembic current
```

---

## Troubleshooting

### `password authentication failed for user "postgres"`
PostgreSQL credentials in `.env` don't match the running container.  
Check: `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/passport_db`

### `No OCR engine available`
Tesseract is not installed or not on PATH.  
Run `tesseract --version` to verify. On Windows, check your system PATH.

### `connection refused` on port 5432 or 6379
PostgreSQL or Redis isn't running. Check with `docker ps` and restart if needed:
```bash
docker start passport_db passport_redis
```

### Import errors or missing packages
```bash
uv sync
```

### Clear Python cache
```bash
find . -type d -name __pycache__ -exec rm -rf {} +
```

---

## Decision Outcomes

The system returns one of four outcomes for each document:

| Outcome | Meaning |
|---------|---------|
| `PASS_SCREENING` | All validations passed |
| `FAIL_RULE` | Failed a critical validation rule |
| `REVIEW_REQUIRED` | Warnings present or low confidence |
| `INSUFFICIENT_DATA` | Missing critical data (e.g. no MRZ) |

---

## Key Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/passport_db` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `OCR_ENGINE` | `both` | `tesseract`, `paddle`, or `both` |
| `SECRET_KEY` | *(must change)* | Signing key |
| `ENCRYPTION_KEY` | *(must change)* | Encryption key for sensitive fields |
| `STORAGE_PATH` | `data/uploads` | Where uploaded files are stored |
| `STORAGE_MAX_FILE_SIZE` | `10485760` | Max upload size in bytes (10 MB) |
| `RETENTION_DAYS` | `90` | Days before uploaded files are purged |
| `SYSTEM_ONE_ENABLED` | `false` | Enable external decision model |
| `SYSTEM_ONE_API_URL` | *(empty)* | System One API endpoint |
| `SYSTEM_ONE_API_KEY` | *(empty)* | System One API key |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | `json` | `json` or `text` |
