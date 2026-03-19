from dataclasses import dataclass

from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class BrokerOrderId(ValueObject):
    value: int

    def _validate(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise InvariantViolation("OrderId must be a strict int (not bool)")
        if self.value < 1:
            raise InvariantViolation("OrderId must be ≥ 1")
