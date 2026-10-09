"""Decision service orchestrating the verification workflow."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import EvidenceLedger
from app.core.logging import get_logger
from app.db.models import DecisionOutcome, Document
from app.db.repositories import DecisionRepository, DocumentRepository
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

        # Evaluate policy (deterministic — no external model)
        policy_result = self.policy_engine.evaluate(validation_results=validation_dicts)

        # Record policy evidence
        await EvidenceLedger.add_policy_evidence(
            session=self.session,
            document_id=str(document_id),
            policy_result=policy_result,
        )

        # Convert outcome string to enum
        outcome = DecisionOutcome(policy_result["outcome"])

        # Confidence = validation pass rate
        passed_count = sum(1 for r in validation_results if r.passed)
        overall_confidence = passed_count / len(validation_results) if validation_results else 0.0

        # Create decision record
        decision = await self.decision_repo.create(
            batch_id=uuid.UUID(document.batch_id) if document.batch_id else uuid.uuid4(),
            document_id=document_id,
            outcome=outcome,
            confidence=overall_confidence,
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
            "policy_version": policy_result["policy_version"],
            "triggered_rules": policy_result["triggered_rules"],
            "validation_summary": self.validation_engine.get_summary(validation_results),
        }
