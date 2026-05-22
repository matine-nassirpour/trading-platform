from dataclasses import dataclass

from quantum.domain.market.instrument.constraints.price_constraints import (
    PriceConstraints,
)
from quantum.domain.market.instrument.constraints.volume_constraints import (
    VolumeConstraints,
)
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class InstrumentConstraints(ValueObject):
    price: PriceConstraints
    volume: VolumeConstraints

    def _validate_semantics(self) -> None:
        if not isinstance(self.price, PriceConstraints):
            raise InvariantViolation("price must be PriceConstraints")

        if not isinstance(self.volume, VolumeConstraints):
            raise InvariantViolation("volume must be VolumeConstraints")
