from quantum.domain.market.instrument.instrument_spec import InstrumentSpec
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.trading.execution.order.position_side import PositionSide
from quantum.domain.trading.execution.safety.exit_policy import ExitPolicy


class ExitValidationService:

    @staticmethod
    def validate_exit_prices(
        *,
        side: PositionSide,
        entry: Price,
        sl: Price | None,
        tp: Price | None,
        instrument: InstrumentSpec,
    ) -> None:

        ExitPolicy.validate(
            side=side,
            entry=entry,
            sl=sl,
            tp=tp,
            instrument=instrument,
        )
