from decimal import Decimal

from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService
from quantum.domain.trading.execution.position_side import PositionSide
from quantum.domain.trading.execution.pricing.pricing_context import PricingContext
from quantum.domain.trading.execution.pricing.pricing_policy import PricingPolicy
from quantum.domain.trading.value_objects.volume import PositiveVolume


class PnLService(DomainService):
    """
    Canonical domain service for multi-asset realized PnL computation.

    Formula:
        ticks = (exit_price - entry_price) / price_increment
        pnl   = ticks * tick_value * volume * side_sign

    Rationale:
    - avoids assuming that 1 price point equals 1 monetary unit;
    - supports FX, CFDs, indices, metals, futures-like instruments;
    - uses instrument-defined tick economics;
    - keeps PnL contextual and currency-safe.
    """

    __slots__ = ()

    @staticmethod
    def compute_realized_pnl(
        *,
        entry_price: Price,
        exit_price: Price,
        volume: PositiveVolume,
        side: PositionSide,
        instrument: InstrumentSpec,
    ) -> RealizedPnL:
        """
        Computes realized PnL for a closed position.

        The result is bound to the given MoneyContext.
        """

        q_entry = PricingPolicy.quantize_price(
            value=entry_price.value,
            instrument=instrument,
            context=PricingContext.neutral(),
        )

        q_exit = PricingPolicy.quantize_price(
            value=exit_price.value,
            instrument=instrument,
            context=PricingContext.neutral(),
        )

        price_delta = q_exit - q_entry

        ticks = price_delta / instrument.price_increment

        raw_pnl = (
            ticks * instrument.tick_value.value * volume.value * Decimal(side.sign())
        )

        quantized_pnl = PricingPolicy.quantize_money(
            value=raw_pnl,
            instrument=instrument,
        )

        return RealizedPnL(
            value=quantized_pnl,
            currency=instrument.pnl_currency,
            context=instrument.context,
        )
