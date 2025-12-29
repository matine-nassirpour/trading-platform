from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects._numeric import _NumericValueObject


@dataclass(frozen=True)
class PositiveVolume(_NumericValueObject):
    """
    Volume strictly greater than zero.

    Use cases:
    - requested order volume
    - initial position size
    """

    value: Decimal

    def _validate_type(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("Volume value must be a Decimal")

        if self.value <= Decimal("0"):
            raise InvariantViolation("PositiveVolume must be strictly > 0")


@dataclass(frozen=True)
class NonNegativeVolume(_NumericValueObject):
    """
    Volume greater than or equal to zero.

    Use cases:
    - filled volume
    - partial fills
    - closed volume
    """

    value: Decimal

    def _validate_type(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("Volume value must be a Decimal")

        if self.value < Decimal("0"):
            raise InvariantViolation("NonNegativeVolume must be ≥ 0")

    @classmethod
    def zero(cls) -> NonNegativeVolume:
        return cls(Decimal("0"))
