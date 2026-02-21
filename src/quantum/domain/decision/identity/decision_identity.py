from dataclasses import dataclass

from quantum.domain.decision.identity.decision_confidence import DecisionConfidence
from quantum.domain.decision.identity.decision_source import DecisionSource
from quantum.domain.decision.identity.model_version import ModelVersion
from quantum.domain.decision.identity.strategy_id import StrategyId
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class DecisionIdentity(ValueObject):
    """
    Canonical identity of a trading decision.

    Answers:
    - WHO decided?
    - WHICH logic?
    - WHICH version?
    - WITH WHICH CONFIDENCE?
    - WITH WHICH CAPITAL & RISK ALLOCATION?
    """

    strategy_id: StrategyId
    model_version: ModelVersion
    source: DecisionSource
    confidence: DecisionConfidence

    def _validate(self) -> None:
        if not isinstance(self.strategy_id, StrategyId):
            raise InvariantViolation("DecisionIdentity requires a StrategyId")

        if not isinstance(self.model_version, ModelVersion):
            raise InvariantViolation("DecisionIdentity requires a ModelVersion")

        if not isinstance(self.source, DecisionSource):
            raise InvariantViolation("DecisionIdentity requires a DecisionSource")

        if not isinstance(self.confidence, DecisionConfidence):
            raise InvariantViolation("DecisionIdentity requires DecisionConfidence")
