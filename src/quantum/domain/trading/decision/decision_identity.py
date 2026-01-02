from dataclasses import dataclass

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject
from quantum.domain.trading.decision.decision_source import DecisionSource
from quantum.domain.trading.decision.model_version import ModelVersion
from quantum.domain.trading.decision.strategy_id import StrategyId


@dataclass(frozen=True)
class DecisionIdentity(ValueObject):
    """
    Canonical identity of a trading decision.

    Answers:
    - WHO decided?
    - WHICH logic?
    - WHICH version?
    """

    strategy_id: StrategyId
    model_version: ModelVersion
    source: DecisionSource

    def _validate(self) -> None:
        if not isinstance(self.strategy_id, StrategyId):
            raise InvariantViolation("DecisionIdentity requires a StrategyId")

        if not isinstance(self.model_version, ModelVersion):
            raise InvariantViolation("DecisionIdentity requires a ModelVersion")

        if not isinstance(self.source, DecisionSource):
            raise InvariantViolation("DecisionIdentity requires a DecisionSource")
