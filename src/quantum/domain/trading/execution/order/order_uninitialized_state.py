from dataclasses import dataclass

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.trading.execution.order.order_state_base import OrderStateBase


@dataclass(frozen=True, slots=True)
class OrderUninitializedState(OrderStateBase):

    def _validate(self):
        if not self.last_sequence.is_initial():
            raise InvariantViolation("Uninitialized Order must have initial sequence")
