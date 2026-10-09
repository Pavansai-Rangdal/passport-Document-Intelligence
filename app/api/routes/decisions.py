"""Decision endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import AuditLogger
from app.db.repositories import DocumentRepository
from app.db.session import get_session
from app.decision import DecisionService
from app.schemas import DecisionResponse

router = APIRouter()


@router.post("/documents/{document_id}/decide", response_model=DecisionResponse)
async def make_decision(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> DecisionResponse:
    """Make a verification decision for a document."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document ID")

    doc_repo = DocumentRepository(session)
    document = await doc_repo.get_by_id(doc_uuid)

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # For now, we'll need extraction data
    # In a real implementation, this would be retrieved from the database
    extraction_data = {
        "mrz_detected": document.mrz_detected,
        "mrz_data": {},
        "ocr_fields": {},
        "normalized_fields": {},
        "quality": {
            "width": document.width,
            "height": document.height,
            "blur_score": document.blur_score,
            "brightness": document.brightness,
            "quality_passed": document.quality_passed,
        },
    }

    # Get fields from database

    mrz_data = {}
    for field in document.fields:
        if field.field_type.value == "document_number":
            mrz_data["document_number"] = field.value
        elif field.field_type.value == "issuing_state":
            mrz_data["issuing_state"] = field.value
        elif field.field_type.value == "birth_date":
            mrz_data["birth_date"] = field.value
        elif field.field_type.value == "expiry_date":
            mrz_data["expiry_date"] = field.value
        elif field.field_type.value == "sex":
            mrz_data["sex"] = field.value

    extraction_data["mrz_data"] = mrz_data

    decision_service = DecisionService(session)
    try:
        decision = await decision_service.make_decision(doc_uuid, extraction_data)
        await AuditLogger.log_decision_made(
            session=session,
            document_id=document_id,
            outcome=decision["outcome"],
        )
        await session.commit()
        return DecisionResponse(**decision)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
