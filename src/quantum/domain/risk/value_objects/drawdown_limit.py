from decimal import Decimal

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey
from quantum.domain.shared_kernel.value_objects.currency import Currency


@immutable_dataclass
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

    def _monetary_kind(self) -> None:
        pass

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    def _validate_semantics(self, key: MutationKey) -> None:
        super()._validate_semantics(key)

        if self.value <= Decimal("0"):
            raise InvariantViolation("DrawdownLimit must be strictly positive")
