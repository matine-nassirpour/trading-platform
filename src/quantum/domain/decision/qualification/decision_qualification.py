from dataclasses import dataclass

from quantum.domain.decision.qualification.decision_confidence import DecisionConfidence
from quantum.domain.decision.qualification.decision_source import DecisionSource
from quantum.domain.decision.qualification.model_version import ModelVersion
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class DecisionQualification(ValueObject):
    """
    Canonical qualification of a trading decision.

    Answers:
    - WHICH strategy produced the decision?
    - WHICH model / logic version produced it?
    - FROM WHICH source did it originate?
    - WITH WHICH declared confidence was it emitted?
    """

    strategy_id: StrategyId
    model_version: ModelVersion
    source: DecisionSource
    confidence: DecisionConfidence

    def _validate_semantics(self) -> None:
        if not isinstance(self.strategy_id, StrategyId):
            raise InvariantViolation("DecisionQualification requires a StrategyId")

        if not isinstance(self.model_version, ModelVersion):
            raise InvariantViolation("DecisionQualification requires a ModelVersion")

        if not isinstance(self.source, DecisionSource):
            raise InvariantViolation("DecisionQualification requires a DecisionSource")

        if not isinstance(self.confidence, DecisionConfidence):
            raise InvariantViolation(
                "DecisionQualification requires DecisionConfidence"
            )
