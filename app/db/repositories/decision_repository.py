"""Decision repository for database operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import DecisionOutcome, DecisionRecord

logger = get_logger(__name__)


class DecisionRepository:
    """Repository for decision record operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        batch_id: uuid.UUID,
        document_id: uuid.UUID,
        outcome: DecisionOutcome,
        confidence: float,
        system_one_recommendation: str | None = None,
        system_one_confidence: float | None = None,
        policy_version: str | None = None,
        policy_rules_triggered: list[str] | None = None,
        reasoning: str | None = None,
        decision_metadata: dict | None = None,
    ) -> DecisionRecord:
        """Create a new decision record."""
        decision = DecisionRecord(
            batch_id=str(batch_id),
            document_id=str(document_id),
            outcome=outcome,
            confidence=confidence,
            system_one_recommendation=system_one_recommendation,
            system_one_confidence=system_one_confidence,
            policy_version=policy_version,
            policy_rules_triggered=policy_rules_triggered,
            reasoning=reasoning,
            decision_metadata=decision_metadata,
        )
        self.session.add(decision)
        await self.session.flush()
        await self.session.refresh(decision)
        logger.info(
            "Decision record created",
            decision_id=str(decision.id),
            document_id=str(document_id),
            outcome=outcome.value,
        )
        return decision

    async def get_by_id(self, decision_id: uuid.UUID) -> DecisionRecord | None:
        """Get decision record by ID."""
        stmt = select(DecisionRecord).where(DecisionRecord.id == decision_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_document_id(self, document_id: uuid.UUID) -> DecisionRecord | None:
        """Get decision record by document ID."""
        stmt = select(DecisionRecord).where(DecisionRecord.document_id == str(document_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_batch_id(self, batch_id: uuid.UUID) -> list[DecisionRecord]:
        """Get all decision records for a batch."""
        stmt = select(DecisionRecord).where(DecisionRecord.batch_id == str(batch_id))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
