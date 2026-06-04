from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class PositionCloseOutcome(ValueObject):
    """
    Semantic domain outcome of closing a Position.

    Application handlers must consume this outcome instead of inspecting
    concrete Position event types.
    """

    realized_pnl: RealizedPnL

    def _validate_semantics(self) -> None:
        if not isinstance(self.realized_pnl, RealizedPnL):
            raise InvariantViolation(
                "PositionCloseOutcome.realized_pnl must be RealizedPnL"
            )
