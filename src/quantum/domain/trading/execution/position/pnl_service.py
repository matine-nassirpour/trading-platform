from decimal import Decimal

from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
from quantum.domain.shared_kernel.modeling.monetary.pnl import RealizedPnL
from quantum.domain.shared_kernel.modeling.monetary.price import Price
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService
from quantum.domain.trading.execution.position_side import PositionSide
from quantum.domain.trading.execution.pricing.pricing_policy import PricingPolicy
from quantum.domain.trading.value_objects.volume import PositiveVolume


class PnLService(DomainService):
    """
    Canonical domain service for PnL computation.

    HARD GUARANTEES:
    - PnL is always contextual (MoneyContext-bound)
    - Currency-safe
    - Deterministic
    - Sign-correct (LONG / SHORT)
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

        Formula:
            pnl = (exit_price - entry_price) * volume * side_sign

        The result is bound to the given MoneyContext.
        """

        price_delta = exit_price.value - entry_price.value
        raw_pnl = (
            price_delta
            * volume.value
            * instrument.contract_size.value
            * Decimal(side.sign())
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
