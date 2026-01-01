from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.shared.errors.invariants import InvariantViolation
from quantum.domain.shared.primitives.value_object import ValueObject
from quantum.domain.shared.value_objects.currency import Currency
from quantum.domain.shared.value_objects.symbol import Symbol
from quantum.domain.trading.value_objects.instrument.currency_pair import CurrencyPair
from quantum.domain.trading.value_objects.market.contract_size import ContractSize
from quantum.domain.trading.value_objects.market.tick_value import TickValue
from quantum.domain.trading.value_objects.market.volume_constraints import (
    VolumeConstraints,
)
from quantum.domain.trading.value_objects.pricing.price_constraints import (
    PriceConstraints,
)


@dataclass(frozen=True)
class InstrumentSpec(ValueObject):
    """
    Canonical institutional-grade tradable instrument specification.

    Design goals:
    - Broker-agnostic
    - Audit-safe
    - Multi-asset compatible (FX, CFD, Futures)
    """

    symbol: Symbol

    # --- Market mechanics
    price_increment: Decimal
    volume_increment: Decimal

    price_scale: Decimal
    volume_scale: Decimal
    money_scale: Decimal

    # --- Trading constraints
    volume_constraints: VolumeConstraints
    price_constraints: PriceConstraints

    # --- Economics
    contract_size: ContractSize
    tick_value: TickValue

    # --- Currencies
    currencies: CurrencyPair
    pnl_currency: Currency

    # --- Invariants ----------------------------------------------------------

    @staticmethod
    def _validate_positive_decimal(value: Decimal, name: str) -> None:
        if not isinstance(value, Decimal):
            raise InvariantViolation(f"{name} must be a Decimal")
        if value <= Decimal("0"):
            raise InvariantViolation(f"{name} must be strictly positive")

    def _validate(self) -> None:
        # increments & scales
        self._validate_positive_decimal(self.price_increment, "price_increment")
        self._validate_positive_decimal(self.volume_increment, "volume_increment")

        self._validate_positive_decimal(self.price_scale, "price_scale")
        self._validate_positive_decimal(self.volume_scale, "volume_scale")
        self._validate_positive_decimal(self.money_scale, "money_scale")

        # currencies
        if self.tick_value.currency != self.pnl_currency:
            raise InvariantViolation("TickValue currency must match PnL currency")

        if self.pnl_currency not in {
            self.currencies.base,
            self.currencies.quote,
        }:
            raise InvariantViolation(
                "PnL currency must be either base or quote currency"
            )
