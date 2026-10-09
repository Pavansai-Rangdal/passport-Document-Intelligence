"""Evidence ledger for verification evidence."""

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import Evidence, EvidenceType

logger = get_logger(__name__)


class EvidenceLedger:
    """Manages evidence collected during verification."""

    @staticmethod
    async def add_evidence(
        session: AsyncSession,
        document_id: str,
        evidence_type: EvidenceType,
        source: str,
        data: dict[str, Any],
        confidence: float | None = None,
        timestamp: str | None = None,
    ) -> Evidence:
        """Add evidence to the ledger."""
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()

        evidence = Evidence(
            document_id=document_id,
            evidence_type=evidence_type,
            source=source,
            data=data,
            confidence=confidence,
            timestamp=timestamp,
        )

        session.add(evidence)
        await session.flush()
        await session.refresh(evidence)

        logger.info(
            "Evidence added",
            document_id=document_id,
            evidence_type=evidence_type.value,
            source=source,
        )

        return evidence

    @staticmethod
    async def add_image_quality_evidence(
        session: AsyncSession,
        document_id: str,
        quality_data: dict[str, Any],
    ) -> Evidence:
        """Add image quality evidence."""
        return await EvidenceLedger.add_evidence(
            session=session,
            document_id=document_id,
            evidence_type=EvidenceType.IMAGE_QUALITY,
            source="quality_assessor",
            data=quality_data,
        )

    @staticmethod
    async def add_mrz_evidence(
        session: AsyncSession,
        document_id: str,
        mrz_data: dict[str, Any],
        confidence: float | None = None,
    ) -> Evidence:
        """Add MRZ extraction evidence."""
        return await EvidenceLedger.add_evidence(
            session=session,
            document_id=document_id,
            evidence_type=EvidenceType.MRZ_DETECTED,
            source="mrz_parser",
            data=mrz_data,
            confidence=confidence,
        )

    @staticmethod
    async def add_ocr_evidence(
        session: AsyncSession,
        document_id: str,
        ocr_data: dict[str, Any],
        engine: str,
        confidence: float | None = None,
    ) -> Evidence:
        """Add OCR extraction evidence."""
        return await EvidenceLedger.add_evidence(
            session=session,
            document_id=document_id,
            evidence_type=EvidenceType.OCR_EXTRACTION,
            source=f"ocr_{engine}",
            data=ocr_data,
            confidence=confidence,
        )

    @staticmethod
    async def add_validation_evidence(
        session: AsyncSession,
        document_id: str,
        validation_results: list[dict[str, Any]],
    ) -> Evidence:
        """Add validation evidence."""
        return await EvidenceLedger.add_evidence(
            session=session,
            document_id=document_id,
            evidence_type=EvidenceType.FIELD_CONSISTENCY,
            source="validation_engine",
            data={"results": validation_results},
        )

    @staticmethod
    async def add_policy_evidence(
        session: AsyncSession,
        document_id: str,
        policy_result: dict[str, Any],
    ) -> Evidence:
        """Add policy evaluation evidence."""
        return await EvidenceLedger.add_evidence(
            session=session,
            document_id=document_id,
            evidence_type=EvidenceType.POLICY_EVALUATION,
            source="policy_engine",
            data=policy_result,
        )
