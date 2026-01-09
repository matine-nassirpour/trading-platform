from __future__ import annotations

from decimal import Decimal

from quantum.domain.shared_kernel.architecture.domain_charter import DomainRole
from quantum.domain.shared_kernel.architecture.domain_object import DomainObject
from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.shared_kernel.value_objects.realized_pnl import RealizedPnL
from quantum.domain.shared_kernel.value_objects.volume import PositiveVolume
from quantum.domain.trading.execution.order.position_side import PositionSide


class PnLService(DomainObject):
    """
    Canonical domain service for PnL computation.

    HARD GUARANTEES:
    - PnL is always contextual (MoneyContext-bound)
    - Currency-safe
    - Deterministic
    - Sign-correct (LONG / SHORT)
    """

    @classmethod
    def role(cls) -> DomainRole:
        return DomainRole.SERVICE

    @staticmethod
    def compute_realized_pnl(
        *,
        entry_price: Price,
        exit_price: Price,
        volume: PositiveVolume,
        side: PositionSide,
        context: MoneyContext,
    ) -> RealizedPnL:
        """
        Computes realized PnL for a closed position.

        Formula:
            pnl = (exit_price - entry_price) * volume * side_sign

        The result is bound to the given MoneyContext.
        """

        if not isinstance(context, MoneyContext):
            raise InvariantViolation("PnLService requires a MoneyContext")

        delta = exit_price.value - entry_price.value
        pnl_value = delta * volume.value * Decimal(side.sign())

        return RealizedPnL(
            value=pnl_value,
            currency=context.reporting_currency,
            context=context,
        )
