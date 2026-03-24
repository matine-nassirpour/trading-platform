from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.ddd.value_objects.value_object import ValueObject
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation


@dataclass(frozen=True, slots=True)
class VolumeConstraints(ValueObject):
    """
    Canonical volume constraints for an instrument.
    """

    min_volume: Decimal
    max_volume: Decimal

    def _validate_semantics(self) -> None:
        for name, v in {
            "min_volume": self.min_volume,
            "max_volume": self.max_volume,
        }.items():
            if not isinstance(v, Decimal):
                raise InvariantViolation(f"{name} must be a Decimal")

            if v <= Decimal("0"):
                raise InvariantViolation(f"{name} must be strictly positive")

        if self.min_volume > self.max_volume:
            raise InvariantViolation("min_volume cannot exceed max_volume")
