from dataclasses import dataclass

from quantum.domain.decision.lifecycle.strategy_lifecycle_state import (
    StrategyLifecycleState,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.identity.strategy_id import StrategyId
from quantum.domain.shared_kernel.modeling.temporal.temporal_validity import (
    TemporalValidity,
)
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


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

    def _validate_semantics(self) -> None:
        if not isinstance(self.strategy_id, StrategyId):
            raise InvariantViolation("StrategyLifecycle requires a StrategyId")

        if not isinstance(self.state, StrategyLifecycleState):
            raise InvariantViolation("Invalid StrategyLifecycleState")

        if not isinstance(self.validity, TemporalValidity):
            raise InvariantViolation("StrategyLifecycle requires TemporalValidity")
