from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class VolumeConstraints(ValueObject):
    min_volume: Decimal
    max_volume: Decimal
    volume_step: Decimal

    def _validate_semantics(self) -> None:
        for name, value in {
            "min_volume": self.min_volume,
            "max_volume": self.max_volume,
            "volume_step": self.volume_step,
        }.items():
            if not isinstance(value, Decimal):
                raise InvariantViolation(f"{name} must be a Decimal")

            if value <= Decimal("0"):
                raise InvariantViolation(f"{name} must be strictly positive")

        if self.min_volume > self.max_volume:
            raise InvariantViolation("min_volume cannot exceed max_volume")

        if self.volume_step > self.max_volume:
            raise InvariantViolation("volume_step cannot exceed max_volume")
