from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.value_objects.numeric_value_object import (
    NumericValueObject,
)


@dataclass(frozen=True, slots=True)
class ContractSize(NumericValueObject):
    """
    Number of underlying units per contract / lot.
    """

    @classmethod
    def nominal_type(cls) -> str:
        return "contract_size"

    def _validate_numeric_semantics(self) -> None:
        super()._validate_numeric_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("ContractSize must be strictly positive")
