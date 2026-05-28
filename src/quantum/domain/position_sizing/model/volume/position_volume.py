from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.market.instrument.volume.volume_unit import VolumeUnit
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True, slots=True)
class PositionVolume(NumericValueObject):
    """
    Final executable position volume in broker/instrument volume units.

    This is NOT an order.
    It is the risk-approved quantity that trading may later transform
    into an executable order instruction.
    """

    unit: VolumeUnit

    @classmethod
    def nominal_type(cls) -> str:
        return "position_volume"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("PositionVolume must be strictly positive")

        if not isinstance(self.unit, VolumeUnit):
            raise InvariantViolation("PositionVolume.unit must be VolumeUnit")
