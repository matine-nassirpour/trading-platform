from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.base import ValueObject


@dataclass(frozen=True)
class VolumeConstraints(ValueObject):
    """
    Canonical volume constraints for an instrument.
    """

    min_volume: Decimal
    max_volume: Decimal

    def _validate(self) -> None:
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
