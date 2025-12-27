from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject
from quantum.domain.policies.monetary_policy import MonetaryPolicy


@dataclass(frozen=True)
class Volume(ValueObject):
    value: Decimal

    def _validate(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("Volume value must be a Decimal")

        quantized = MonetaryPolicy.quantize_volume(self.value)

        if quantized <= Decimal("0"):
            raise InvariantViolation("Volume must be strictly positive")

        object.__setattr__(self, "value", quantized)

    @classmethod
    def zero(cls) -> Volume:
        return cls(Decimal("0.0"))
