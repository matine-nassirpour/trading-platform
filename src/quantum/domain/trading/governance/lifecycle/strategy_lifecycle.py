from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.value_object import ValueObject
from quantum.domain.shared_kernel.temporal.temporal_validity import TemporalValidity
from quantum.domain.trading.core.decision.identity.strategy_id import StrategyId
from quantum.domain.trading.governance.lifecycle.strategy_lifecycle_state import (
    StrategyLifecycleState,
)


@dataclass(frozen=True, slots=True)
class StrategyLifecycle(ValueObject):
    """
    Canonical lifecycle contract for a trading strategy or model.

    Answers:
        "Is this strategy allowed to produce decisions at this time?"
    """

    strategy_id: StrategyId
    state: StrategyLifecycleState
    validity: TemporalValidity

    def _validate(self) -> None:
        if not isinstance(self.strategy_id, StrategyId):
            raise InvariantViolation("StrategyLifecycle requires a StrategyId")

        if not isinstance(self.state, StrategyLifecycleState):
            raise InvariantViolation("Invalid StrategyLifecycleState")

        if not isinstance(self.validity, TemporalValidity):
            raise InvariantViolation("StrategyLifecycle requires TemporalValidity")
