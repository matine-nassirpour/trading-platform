from __future__ import annotations

from decimal import Decimal

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.immutable_dataclass import (
    immutable_dataclass,
)
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.contextual_monetary_amount import (
    ContextualMonetaryAmount,
)
from quantum.domain.shared_kernel.primitives.mutation_key import MutationKey


@immutable_dataclass
class Drawdown(ContextualMonetaryAmount):
    """
    Drawdown = equity_peak − equity.

    Properties:
    - Always ≥ 0
    - Bound to a MoneyContext
    - Non-algebraic
    """

    def _monetary_kind(self) -> None:
        pass

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.VALUE_OBJECT

    def _validate_semantics(self, key: MutationKey) -> None:
        super()._validate_semantics(key)

        if self.value < Decimal("0"):
            raise InvariantViolation("Drawdown must be non-negative")
