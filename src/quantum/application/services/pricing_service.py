from decimal import Decimal

from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
from quantum.domain.trading.execution.order.position_side import PositionSide
from quantum.domain.trading.execution.pricing.pricing_context import PricingContext
from quantum.domain.trading.execution.pricing.pricing_policy import PricingPolicy


class PricingService:

    @staticmethod
    def quantize_price(
        *,
        value: Decimal,
        instrument: InstrumentSpec,
        context: PricingContext,
        side: PositionSide | None = None,
    ) -> Decimal:

        return PricingPolicy.quantize_price(
            value=value,
            instrument=instrument,
            context=context,
            side=side,
        )
