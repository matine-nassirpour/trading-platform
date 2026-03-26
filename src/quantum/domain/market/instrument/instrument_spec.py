from dataclasses import dataclass
from decimal import Decimal

from quantum.domain.market.instrument.currency.currency_pair import CurrencyPair
from quantum.domain.market.instrument.identity.symbol import Symbol
from quantum.domain.market.instrument.pricing.price_constraints import PriceConstraints
from quantum.domain.market.instrument.pricing.tick_value import TickValue
from quantum.domain.market.instrument.sizing.contract_size import ContractSize
from quantum.domain.market.instrument.sizing.volume_constraints import VolumeConstraints
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.monetary.currency import Currency
from quantum.domain.shared_kernel.modeling.monetary.money_context import MoneyContext
from quantum.domain.shared_kernel.modeling.value_objects.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class InstrumentSpec(ValueObject):
    """
    Canonical institutional-grade tradable instrument specification.

    Design goals:
    - Broker-agnostic
    - Audit-safe
    - Multi-asset compatible (FX, CFD, Futures)
    """

    symbol: Symbol

    context: MoneyContext

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

    # --- Invariants -----------------------------------------------------------

    @staticmethod
    def _validate_positive_decimal(value: Decimal, name: str) -> None:
        if not isinstance(value, Decimal):
            raise InvariantViolation(f"{name} must be a Decimal")
        if value <= Decimal("0"):
            raise InvariantViolation(f"{name} must be strictly positive")

    def _validate_semantics(self) -> None:
        if not isinstance(self.context, MoneyContext):
            raise InvariantViolation("InstrumentSpec requires a MoneyContext")

        # increments & scales
        self._validate_positive_decimal(self.price_increment, "price_increment")
        self._validate_positive_decimal(self.volume_increment, "volume_increment")
        self._validate_positive_decimal(self.price_scale, "price_scale")
        self._validate_positive_decimal(self.volume_scale, "volume_scale")
        self._validate_positive_decimal(self.money_scale, "money_scale")

        # TickValue and PnL must belong to this ledger
        if self.tick_value.currency != self.context.reporting_currency:
            raise InvariantViolation(
                "TickValue currency must match MoneyContext reporting currency"
            )

        if self.pnl_currency != self.context.reporting_currency:
            raise InvariantViolation(
                "PnL currency must match MoneyContext reporting currency"
            )

        # FX semantics still enforced
        if self.pnl_currency not in {
            self.currencies.base,
            self.currencies.quote,
        }:
            raise InvariantViolation(
                "PnL currency must be either base or quote currency"
            )
