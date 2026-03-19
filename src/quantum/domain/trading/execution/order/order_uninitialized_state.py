from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.trading.execution.order.order_state_base import OrderStateBase


@dataclass(frozen=True, slots=True)
class OrderUninitializedState(OrderStateBase):
    """
    Order state before the first domain event has been applied.
    """

    def _validate(self) -> None:
        super()._validate()

        if not self.last_sequence.is_initial():
            raise InvariantViolation("Uninitialized Order must have initial sequence")
