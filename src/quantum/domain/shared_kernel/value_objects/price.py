from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)


@dataclass(frozen=True)
class Price(ContextualMonetaryAmount):
    """
    Strictly positive monetary quantity.
    """

    value: Decimal

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("Price must be strictly positive")
