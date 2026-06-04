from dataclasses import dataclass

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject
from quantum.domain.trading.common.value_objects.volume import NonNegativeVolume
from quantum.domain.trading.order.status.order_fill_status import OrderFillStatus
from quantum.domain.trading.order.status.order_lifecycle_status import (
    OrderLifecycleStatus,
)


@dataclass(frozen=True, slots=True)
class OrderFillOutcome(ValueObject):
    """
    Semantic domain outcome of registering an order fill.

    Application handlers must consume this outcome instead of reconstructing
    future order state from current state + emitted events.
    """

    filled_volume: NonNegativeVolume
    fill_status: OrderFillStatus
    lifecycle_status: OrderLifecycleStatus

    def _validate_semantics(self) -> None:
        if not isinstance(self.filled_volume, NonNegativeVolume):
            raise InvariantViolation("OrderFillOutcome.filled_volume invalid")

        if not isinstance(self.fill_status, OrderFillStatus):
            raise InvariantViolation("OrderFillOutcome.fill_status invalid")

        if not isinstance(self.lifecycle_status, OrderLifecycleStatus):
            raise InvariantViolation("OrderFillOutcome.lifecycle_status invalid")

        if self.fill_status.is_filled():
            if self.lifecycle_status != OrderLifecycleStatus.completed():
                raise InvariantViolation(
                    "Filled OrderFillOutcome requires completed lifecycle status"
                )

        if self.lifecycle_status == OrderLifecycleStatus.completed():
            if not self.fill_status.is_filled():
                raise InvariantViolation(
                    "Completed OrderFillOutcome requires filled status"
                )
