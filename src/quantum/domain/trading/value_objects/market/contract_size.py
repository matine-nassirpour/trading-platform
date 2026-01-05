from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.primitives.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True)
class ContractSize(NumericValueObject):
    """
    Number of underlying units per contract / lot.
    """

    value: Decimal

    def _validate_semantics(self) -> None:
        if self.value <= Decimal("0"):
            raise InvariantViolation("ContractSize must be strictly positive")
