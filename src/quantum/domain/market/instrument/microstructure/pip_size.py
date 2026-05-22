from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True, slots=True)
class PipSize(NumericValueObject):
    """
    FX pip size.

    This is optional at InstrumentMicrostructure level because not every
    instrument has a meaningful pip concept.
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "pip_size"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("PipSize must be strictly positive")
