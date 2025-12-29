from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects._numeric import _NumericValueObject


@dataclass(frozen=True)
class ReferencePrice(_NumericValueObject):
    """
    Non-executable price used as a decision or market snapshot reference.
    """

    value: Decimal

    def _validate_type(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvariantViolation("ReferencePrice value must be a Decimal")

        if self.value <= Decimal("0"):
            raise InvariantViolation("ReferencePrice must be strictly positive")
