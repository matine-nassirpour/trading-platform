from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.value_objects.currency import Currency


@dataclass(frozen=False)
class DrawdownLimit(ContextualMonetaryAmount):
    """
    Maximum allowed drawdown.

    Properties:
    - Monetary threshold
    - Strictly positive
    - Non-algebraic
    """

    value: Decimal
    currency: Currency
    context: MoneyContext

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    def _validate_semantics(self) -> None:
        super()._validate_semantics()

        if self.value <= Decimal("0"):
            raise InvariantViolation("DrawdownLimit must be strictly positive")
