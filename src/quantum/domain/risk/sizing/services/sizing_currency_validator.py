from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
from quantum.domain.risk.governance.measures.equity import Equity
from quantum.domain.shared_kernel.foundation.errors.invariants import (
    CurrencyMismatch,
    InvariantViolation,
)
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService


class SizingCurrencyValidator(DomainService):
    """
    Enforces that all monetary quantities used by PositionSizer are expressed
    in the same risk/PnL currency.

    Required because:
        risk_amount = equity * risk_budget
        risk_per_volume = ticks * tick_value
        volume = risk_amount / risk_per_volume

    Therefore:
        equity.currency == instrument.microstructure.tick_value.currency
        equity.currency == instrument.currencies.pnl_currency
    """

    __slots__ = ()

    @staticmethod
    def validate(
        *,
        equity: Equity,
        instrument: InstrumentSpec,
    ) -> None:
        if equity.context != instrument.context:
            raise InvariantViolation("Equity MoneyContext mismatch with instrument")

        pnl_currency = instrument.currencies.pnl_currency
        tick_value_currency = instrument.microstructure.tick_value.currency
        point_value_currency = instrument.microstructure.point_value.currency

        if equity.currency != pnl_currency:
            raise CurrencyMismatch("Equity currency must equal instrument pnl_currency")

        if tick_value_currency != pnl_currency:
            raise CurrencyMismatch(
                "tick_value.currency must equal instrument pnl_currency"
            )

        if point_value_currency != pnl_currency:
            raise CurrencyMismatch(
                "point_value.currency must equal instrument pnl_currency"
            )
