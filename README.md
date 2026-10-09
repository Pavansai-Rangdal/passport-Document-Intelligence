# Passport Document Intelligence

A production-ready, secure document-intelligence pipeline for passport image extraction, validation, and evidence-based decisions using Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Redis, Celery, OpenCV, Pillow, PyMuPDF, and interchangeable OCR engines (PaddleOCR and Tesseract).

## Features

- **Secure File Intake**: Upload validation, malware detection, deduplication via SHA-256 hashing
- **Document Detection**: OpenCV-based boundary detection and MRZ (Machine Readable Zone) detection
- **Image Quality Assessment**: Blur detection, brightness analysis, dimension validation
- **Dual OCR Engines**: Support for PaddleOCR and Tesseract with automatic fallback
- **MRZ Parsing**: ICAO Doc 9303 compliant TD1, TD2, and TD3 format parsing
- **Check Digit Validation**: Full ICAO MRZ checksum validation
- **Field Extraction & Normalization**: Extracted fields with date and field normalization
- **Comprehensive Validation**: Schema, expiry, image quality, cross-field, MRZ checksum, and consistency rules
- **Verification Providers**: Capability registry for external verification services
- **System One Integration**: Typed adapter for external decision model integration
- **Deterministic Policy Engine**: Independent policy engine with PASS_SCREENING, FAIL_RULE, REVIEW_REQUIRED, and INSUFFICIENT_DATA outcomes
- **Evidence Ledger**: Complete audit trail of all verification evidence
- **Background Processing**: Celery-based async document processing
- **Data Retention**: Configurable retention policies for documents and audit logs
- **REST API**: FastAPI-based RESTful API for all operations
- **Docker Support**: Complete Docker Compose deployment

## Architecture

The system follows a modular architecture with clear separation of concerns:

```
app/
├── api/                    # FastAPI routes and endpoints
├── audit/                  # Audit logging and evidence ledger
├── core/                   # Configuration, logging, security
├── db/                     # Database models, session, repositories
├── decision/               # Decision service and System One integration
├── document_processing/    # Document detection, preprocessing, PDF rendering
├── extraction/             # OCR engines, MRZ parsing, field normalization
├── intake/                 # File validation, batch management
├── policy/                 # Deterministic policy engine
├── reporting/              # Batch report generation
├── schemas/                # Pydantic schemas for API
├── storage/                # Object store and retention policies
├── utils/                  # Identifier generation
├── validation/             # Validation engine and rules
├── verification/           # Verification provider registry
└── workers/                # Celery background tasks
```

## Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- uv (Python package manager)
- (Optional) Tesseract OCR binary for Tesseract engine
- (Optional) CUDA for PaddleOCR GPU acceleration

## Installation

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Passport-Document-Intelligence
   ```

2. **Install dependencies with uv**:
   ```bash
   uv sync
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up PostgreSQL**:
   ```bash
   # Using Docker
   docker run -d --name passport_db \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=passport_db \
     -p 5432:5432 \
     postgres:16-alpine
   ```

5. **Set up Redis**:
   ```bash
   docker run -d --name passport_redis -p 6379:6379 redis:7-alpine
   ```

6. **Run database migrations**:
   ```bash
   uv run alembic upgrade head
   ```

7. **Start the application**:
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Docker Deployment

1. **Build and start services**:
   ```bash
   docker-compose up -d
   ```

2. **Run migrations**:
   ```bash
   docker-compose exec web uv run alembic upgrade head
   ```

3. **Access the API**:
   ```
   http://localhost:8000
   http://localhost:8000/docs (Swagger UI)
   ```

## Configuration

Key environment variables (see `.env.example`):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `CELERY_BROKER_URL`: Celery broker URL
- `CELERY_RESULT_BACKEND`: Celery result backend
- `OCR_ENGINE`: `paddle`, `tesseract`, or `both`
- `STORAGE_MAX_FILE_SIZE`: Maximum upload size in bytes (default: 10MB)
- `RETENTION_DAYS`: Document retention period (default: 90 days)
- `SYSTEM_ONE_ENABLED`: Enable System One integration
- `SYSTEM_ONE_API_URL`: System One API endpoint
- `SYSTEM_ONE_API_KEY`: System One API key

## API Usage

### Health Check
```bash
GET /health
```

### Upload Document
```bash
POST /api/v1/upload
Content-Type: multipart/form-data

file: <passport_image>
```

Response:
```json
{
  "document_id": "uuid",
  "internal_id": "doc_20261009_1200_abc123",
  "filename": "passport.jpg",
  "status": "uploaded",
  "created_at": "2026-10-09T12:00:00Z"
}
```

### Get Document
```bash
GET /api/v1/documents/{document_id}
```

### Extract Data
```bash
POST /api/v1/documents/{document_id}/extract
```

Response:
```json
{
  "document_id": "uuid",
  "mrz_detected": true,
  "mrz_data": {
    "document_type": "P",
    "issuing_state": "USA",
    "document_number": "A12345678",
    "birth_date": "1980-01-01",
    "expiry_date": "2030-01-01",
    "sex": "M"
  },
  "ocr_fields": {...},
  "quality": {...}
}
```

### Make Decision
```bash
POST /api/v1/documents/{document_id}/decide
```

Response:
```json
{
  "decision_id": "uuid",
  "outcome": "pass_screening",
  "confidence": 0.95,
  "reasoning": "All validations passed",
  "system_one_recommendation": "pass",
  "policy_version": "1.0",
  "triggered_rules": []
}
```

### Batch Operations
```bash
# Create batch
POST /api/v1/batches

# Get batch status
GET /api/v1/batches/{batch_id}
```

## Decision Outcomes

The system returns one of four deterministic outcomes:

- **PASS_SCREENING**: Document passed all validation rules
- **FAIL_RULE**: Document failed critical validation rules
- **REVIEW_REQUIRED**: Document has warnings or low confidence
- **INSUFFICIENT_DATA**: Missing critical data (e.g., no MRZ)

## Policy Rules

The policy engine applies deterministic rules in order:

1. Critical validation errors → FAIL_RULE
2. System One high-confidence fail → FAIL_RULE
3. System One review recommendation → REVIEW_REQUIRED
4. System One low confidence → REVIEW_REQUIRED
5. Validation warnings → REVIEW_REQUIRED
6. Insufficient MRZ data → INSUFFICIENT_DATA
7. All validations passed → PASS_SCREENING

## OCR Engine Installation

### Tesseract
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### PaddleOCR
```bash
# CPU version
uv sync --extra ocr-paddle

# GPU version (requires CUDA)
uv sync --extra ocr-paddle
```

## Testing

### Run Tests
```bash
uv run pytest tests/
```

### Test Extraction on Sample Files
```bash
uv run python scripts/test_extraction.py
```

### Benchmark OCR Engines
```python
from app.extraction import ExtractionService

service = ExtractionService()
results = service.benchmark_ocr_engines("sample-passports/sample-1.jpg")
print(results)
```

## Integrations Requiring External Credentials

### System One Integration

To enable System One decision model integration:

1. Set environment variables:
   ```
   SYSTEM_ONE_ENABLED=true
   SYSTEM_ONE_API_URL=https://api.system-one.example.com
   SYSTEM_ONE_API_KEY=your-api-key
   ```

2. The system will automatically:
   - Send extraction results, validation findings, and evidence
   - Validate the response structure
   - Pass the recommendation to the independent policy engine

### Chip Authentication

Chip authentication requires:
- NFC reader hardware
- ICAO 9303 compliant ePassport
- Additional configuration (not enabled by default)

### Lost/Stolen Verification

Lost/stolen database verification requires:
- External API credentials
- Country-specific database access
- Additional configuration (not enabled by default)

## Security Considerations

- **File Validation**: All uploads are validated for MIME type, size, and integrity
- **Malware Detection**: Basic malformed file detection
- **Encryption**: Sensitive fields are encrypted at rest
- **Access Control**: API key authentication (optional)
- **Rate Limiting**: Configurable upload rate limits
- **Data Redaction**: Sensitive fields are redacted in logs
- **Retention Policies**: Automatic cleanup of expired data

## Limitations

1. **OCR Availability**: Requires Tesseract binary or PaddleOCR installation
2. **Database Required**: PostgreSQL must be running for full functionality
3. **Sample Files**: The provided sample files may not contain actual MRZ data
4. **External Integrations**: System One, chip auth, and lost/stolen verification require external credentials
5. **Windows Tesseract**: Tesseract binary must be manually installed and added to PATH

## Troubleshooting

### Database Connection Error
```
Error: password authentication failed for user "postgres"
```
Solution: Ensure PostgreSQL is running and credentials match `.env` configuration

### OCR Engine Not Available
```
Error: No OCR engine available or extraction failed
```
Solution: Install Tesseract or PaddleOCR (see OCR Engine Installation section)

### MRZ Not Detected
The sample files may not contain visible MRZ regions. The MRZ detection algorithm looks for:
- Wide, short text regions at the bottom of the image
- Aspect ratio between 5:1 and 15:1
- Height between 20-60 pixels

### Migration Errors
```bash
# Reset migrations
uv run alembic downgrade base
uv run alembic upgrade head
```

## Performance Notes

- **Processing Time**: Extraction typically takes 2-5 seconds per document
- **Memory Usage**: ~200MB per concurrent extraction
- **Database Pool**: Configurable pool size (default: 10 connections)
- **Celery Workers**: Scale workers based on load

## License

Proprietary

## Support

For support, contact the development team or create an issue in the repository.
