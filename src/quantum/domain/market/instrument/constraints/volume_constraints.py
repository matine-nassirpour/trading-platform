from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.market.instrument.volume.volume_unit import VolumeUnit
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class VolumeConstraints(ValueObject):
    min_volume: Decimal
    max_volume: Decimal
    volume_step: Decimal
    volume_step_anchor: Decimal
    volume_unit: VolumeUnit

    def _validate_types(self) -> None:
        for name, value in {
            "min_volume": self.min_volume,
            "max_volume": self.max_volume,
            "volume_step": self.volume_step,
            "volume_step_anchor": self.volume_step_anchor,
        }.items():
            if not isinstance(value, Decimal):
                raise InvariantViolation(f"{name} must be a Decimal")

        if not isinstance(self.volume_unit, VolumeUnit):
            raise InvariantViolation("volume_unit must be VolumeUnit")

    def _validate_semantics(self) -> None:
        self._validate_types()

        if self.min_volume <= Decimal("0"):
            raise InvariantViolation("min_volume must be strictly positive")

        if self.max_volume <= Decimal("0"):
            raise InvariantViolation("max_volume must be strictly positive")

        if self.volume_step <= Decimal("0"):
            raise InvariantViolation("volume_step must be strictly positive")

        if self.volume_step_anchor < Decimal("0"):
            raise InvariantViolation("volume_step_anchor must be non-negative")

        if self.min_volume > self.max_volume:
            raise InvariantViolation("min_volume cannot exceed max_volume")

        if not self.is_step_aligned(self.min_volume):
            raise InvariantViolation("min_volume must be aligned to volume_step_anchor")

        if not self.is_step_aligned(self.max_volume):
            raise InvariantViolation("max_volume must be aligned to volume_step_anchor")

    def is_step_aligned(self, volume: Decimal) -> bool:
        if not isinstance(volume, Decimal):
            raise InvariantViolation("volume must be a Decimal")

        if volume < self.volume_step_anchor:
            return False

        ratio = (volume - self.volume_step_anchor) / self.volume_step
        return ratio == ratio.to_integral_value()
