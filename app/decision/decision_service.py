"""Decision service orchestrating the verification workflow."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import EvidenceLedger
from app.core.exceptions import VerificationError
from app.core.logging import get_logger
from app.db.models import DecisionOutcome, Document
from app.db.repositories import DecisionRepository, DocumentRepository
from app.decision.system_one import SystemOneClient, SystemOneRequest
from app.policy import PolicyEngine
from app.validation import ValidationEngine

logger = get_logger(__name__)


class DecisionService:
    """Service for making verification decisions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.document_repo = DocumentRepository(session)
        self.decision_repo = DecisionRepository(session)
        self.validation_engine = ValidationEngine()
        self.policy_engine = PolicyEngine()
        self.system_one_client = SystemOneClient()

    async def make_decision(
        self,
        document_id: uuid.UUID,
        extraction_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Make a verification decision for a document."""
        logger.info("Making decision", document_id=str(document_id))

        # Get document
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")

        # Run validation
        validation_results = self.validation_engine.validate_document(document, extraction_data)
        validation_dicts = [r.to_dict() for r in validation_results]

        # Record validation evidence
        await EvidenceLedger.add_validation_evidence(
            session=self.session,
            document_id=str(document_id),
            validation_results=validation_dicts,
        )

        # Try System One if available
        system_one_recommendation = None
        system_one_confidence = None

        if self.system_one_client.is_configured():
            try:
                request = SystemOneRequest(
                    document_id=str(document_id),
                    mrz_data=extraction_data.get("mrz_data", {}),
                    ocr_fields=extraction_data.get("ocr_fields", {}),
                    validation_results=validation_dicts,
                    image_quality=extraction_data.get("quality", {}),
                )

                response = await self.system_one_client.get_decision(request)
                system_one_recommendation = response.recommendation
                system_one_confidence = response.confidence

                logger.info(
                    "System One recommendation received",
                    recommendation=system_one_recommendation,
                    confidence=system_one_confidence,
                )

                await EvidenceLedger.add_system_one_evidence(
                    session=self.session,
                    document_id=str(document_id),
                    recommendation=system_one_recommendation,
                    confidence=system_one_confidence,
                    response_data=response.model_dump() if hasattr(response, "model_dump") else {},
                )
            except VerificationError as e:
                logger.warning("System One verification failed", error=str(e))
                # Continue with policy engine only

        # Evaluate policy
        policy_result = self.policy_engine.evaluate(
            validation_results=validation_dicts,
            system_one_recommendation=system_one_recommendation,
            system_one_confidence=system_one_confidence,
        )

        # Record policy evidence
        await EvidenceLedger.add_policy_evidence(
            session=self.session,
            document_id=str(document_id),
            policy_result=policy_result,
        )

        # Convert outcome string to enum
        outcome = DecisionOutcome(policy_result["outcome"])

        # Calculate overall confidence
        # If System One provided confidence, use it; otherwise use validation pass rate
        if system_one_confidence is not None:
            overall_confidence = system_one_confidence
        else:
            passed_count = sum(1 for r in validation_results if r.passed)
            overall_confidence = passed_count / len(validation_results) if validation_results else 0.0

        # Create decision record
        decision = await self.decision_repo.create(
            batch_id=uuid.UUID(document.batch_id) if document.batch_id else uuid.uuid4(),
            document_id=document_id,
            outcome=outcome,
            confidence=overall_confidence,
            system_one_recommendation=system_one_recommendation,
            system_one_confidence=system_one_confidence,
            policy_version=policy_result["policy_version"],
            policy_rules_triggered=policy_result["triggered_rules"],
            reasoning=policy_result["reasoning"],
            decision_metadata={"validation_summary": self.validation_engine.get_summary(validation_results)},
        )

        logger.info(
            "Decision made",
            document_id=str(document_id),
            outcome=outcome.value,
            confidence=overall_confidence,
        )

        return {
            "decision_id": str(decision.id),
            "outcome": outcome.value,
            "confidence": overall_confidence,
            "reasoning": policy_result["reasoning"],
            "system_one_recommendation": system_one_recommendation,
            "system_one_confidence": system_one_confidence,
            "policy_version": policy_result["policy_version"],
            "triggered_rules": policy_result["triggered_rules"],
            "validation_summary": self.validation_engine.get_summary(validation_results),
        }
