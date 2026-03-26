from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class PriceConstraints(ValueObject):
    """
    Broker-enforced price distance constraints.

    stop_level  : minimum distance between market price and SL/TP
    freeze_level: distance within which modification is forbidden
    """

    stop_level: Decimal
    freeze_level: Decimal

    def _validate_semantics(self) -> None:
        for name, v in {
            "stop_level": self.stop_level,
            "freeze_level": self.freeze_level,
        }.items():
            if not isinstance(v, Decimal):
                raise InvariantViolation(f"{name} must be a Decimal")

            if v < Decimal("0"):
                raise InvariantViolation(f"{name} must be non-negative")
