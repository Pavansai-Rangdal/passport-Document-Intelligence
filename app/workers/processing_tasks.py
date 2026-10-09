"""Background processing tasks for Celery."""

import uuid
from pathlib import Path

from celery import Task

from app.db import async_session_maker
from app.db.models import Document, DocumentStatus
from app.db.repositories import BatchRepository, DocumentRepository
from app.extraction import ExtractionService
from app.storage.retention import RetentionManager
from app.workers import celery_app


class DatabaseTask(Task):
    """Base task with database session."""

    _db = None

    @property
    def db(self):
        """Lazy database session."""
        if self._db is None:
            self._db = async_session_maker()
        return self._db


@celery_app.task(bind=True, base=DatabaseTask, name="process_document")
def process_document_task(self, document_id: str) -> dict:
    """Process a document in the background."""
    import asyncio

    async def _process():
        doc_uuid = uuid.UUID(document_id)
        doc_repo = DocumentRepository(self.db)
        document = await doc_repo.get_by_id(doc_uuid)

        if not document:
            return {"error": "Document not found"}

        # Update status to processing
        await doc_repo.update_status(doc_uuid, DocumentStatus.PROCESSING)

        # Perform extraction
        extraction_service = ExtractionService()
        file_path = Path(document.file_path)

        if not file_path.exists():
            await doc_repo.update_status(doc_uuid, DocumentStatus.FAILED, error_message="File not found")
            return {"error": "File not found"}

        try:
            extraction_data = extraction_service.extract_from_image(file_path)

            # Update document with extraction results
            if extraction_data.get("quality"):
                quality = extraction_data["quality"]
                await doc_repo.update_image_quality(
                    document_id=doc_uuid,
                    width=quality.get("width", 0),
                    height=quality.get("height", 0),
                    blur_score=quality.get("blur_score"),
                    brightness=quality.get("brightness"),
                    quality_passed=quality.get("quality_passed"),
                )

            if extraction_data.get("mrz_detected"):
                mrz_data = extraction_data.get("mrz_data")
                await doc_repo.update_mrz_info(
                    document_id=doc_uuid,
                    mrz_detected=True,
                    mrz_type=mrz_data.get("mrz_type") if mrz_data else None,
                )

            # Store extracted fields
            if extraction_data.get("mrz_data"):
                mrz_data = extraction_data["mrz_data"]
                field_mappings = {
                    "document_number": "document_number",
                    "issuing_state": "issuing_state",
                    "birth_date": "birth_date",
                    "expiry_date": "expiry_date",
                    "sex": "sex",
                    "surname": "surname",
                    "given_names": "given_names",
                    "nationality": "nationality",
                }

                for field_name, db_field in field_mappings.items():
                    if mrz_data.get(field_name):
                        await doc_repo.add_field(
                            document_id=doc_uuid,
                            field_type=db_field,
                            field_name=field_name,
                            value=mrz_data[field_name],
                            source="mrz",
                            value_normalized=mrz_data.get(f"{field_name}_normalized"),
                        )

            # Update status to extracted
            await doc_repo.update_status(doc_uuid, DocumentStatus.EXTRACTED)
            await self.db.commit()

            return {
                "document_id": document_id,
                "status": "extracted",
                "mrz_detected": extraction_data.get("mrz_detected"),
            }
        except Exception as e:
            await doc_repo.update_status(doc_uuid, DocumentStatus.FAILED, error_message=str(e))
            await self.db.commit()
            return {"error": str(e)}

    return asyncio.run(_process())


@celery_app.task(bind=True, base=DatabaseTask, name="process_batch")
def process_batch_task(self, batch_id: str) -> dict:
    """Process all documents in a batch."""
    import asyncio

    async def _process():
        batch_uuid = uuid.UUID(batch_id)

        batch_repo = BatchRepository(self.db)

        batch = await batch_repo.get_by_id(batch_uuid)
        if not batch:
            return {"error": "Batch not found"}

        # Process each document
        results = []
        for document in batch.documents:
            if document.status == DocumentStatus.UPLOADED:
                result = process_document_task.apply_async(args=[str(document.id)])
                results.append({"document_id": str(document.id), "task_id": result.id})

        return {
            "batch_id": batch_id,
            "documents_queued": len(results),
            "results": results,
        }

    return asyncio.run(_process())


@celery_app.task(name="run_retention_cleanup")
def run_retention_cleanup() -> dict:
    """Purge expired documents and old audit logs."""
    import asyncio

    async def _cleanup():
        async with async_session_maker() as session:
            doc_result = await RetentionManager.cleanup_expired_documents(session)
            audit_result = await RetentionManager.cleanup_old_audit_logs(session)
            return {
                "documents": doc_result,
                "audit_logs": audit_result,
            }

    return asyncio.run(_cleanup())
