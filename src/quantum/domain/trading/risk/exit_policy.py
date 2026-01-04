from quantum.domain.shared_kernel.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.value_objects.price import Price
from quantum.domain.trading.pricing.pricing_policy import PricingPolicy
from quantum.domain.trading.value_objects.instrument.instrument_spec import (
    InstrumentSpec,
)
from quantum.domain.trading.value_objects.market.reference_price import ReferencePrice
from quantum.domain.trading.value_objects.order.position_side import PositionSide
from quantum.domain.trading.value_objects.pricing.pricing_context import PricingContext


class ExitPolicy:
    """
    Canonical Stop Loss / Take Profit validation policy.

    Design principles:
    - All prices are first quantized using EXECUTABLE directional rounding
    - All comparisons are done on quantized values
    - Ordering rules are side-dependent (LONG / SHORT)
    - SL and TP must never collapse to the same executable tick
    """

    # --- Internal Helpers -----------------------------------------------------

    @staticmethod
    def _quantize_entry(
        *,
        entry: Price | ReferencePrice,
        instrument: InstrumentSpec,
    ) -> Price:
        """
        Entry / reference price is NOT executable.
        Neutral (statistical) quantization only.
        """
        quantized = PricingPolicy.quantize_price(
            value=entry.value,
            instrument=instrument,
            context=PricingContext.neutral(),
        )
        return Price(quantized)

    @staticmethod
    def _quantize_sl_tp(
        *,
        side: PositionSide,
        sl: Price | None,
        tp: Price | None,
        instrument: InstrumentSpec,
    ) -> tuple[Price | None, Price | None]:
        """
        Applies executable, directional quantization to SL / TP.
        """

        q_sl = (
            Price(
                PricingPolicy.quantize_price(
                    value=sl.value,
                    instrument=instrument,
                    context=PricingContext.execution_sl(),
                    side=side,
                )
            )
            if sl is not None
            else None
        )

        q_tp = (
            Price(
                PricingPolicy.quantize_price(
                    value=tp.value,
                    instrument=instrument,
                    context=PricingContext.execution_tp(),
                    side=side,
                )
            )
            if tp is not None
            else None
        )

        return q_sl, q_tp

    @staticmethod
    def _validate_long(
        *,
        entry: Price,
        sl: Price | None,
        tp: Price | None,
        instrument: InstrumentSpec,
    ) -> None:
        if sl and not PricingPolicy.price_less_than(sl.value, entry.value, instrument):
            raise InvariantViolation(
                "LONG position requires SL strictly below entry price "
                "after executable quantization"
            )

        if tp and not PricingPolicy.price_greater_than(
            tp.value, entry.value, instrument
        ):
            raise InvariantViolation(
                "LONG position requires TP strictly above entry price "
                "after executable quantization"
            )

    @staticmethod
    def _validate_short(
        *,
        entry: Price,
        sl: Price | None,
        tp: Price | None,
        instrument: InstrumentSpec,
    ) -> None:
        if sl and not PricingPolicy.price_greater_than(
            sl.value, entry.value, instrument
        ):
            raise InvariantViolation(
                "SHORT position requires SL strictly above entry price "
                "after executable quantization"
            )

        if tp and not PricingPolicy.price_less_than(tp.value, entry.value, instrument):
            raise InvariantViolation(
                "SHORT position requires TP strictly below entry price "
                "after executable quantization"
            )

    @staticmethod
    def _validate_distinct_sl_tp(
        *,
        sl: Price,
        tp: Price,
        instrument: InstrumentSpec,
    ) -> None:
        if PricingPolicy.price_equal(sl.value, tp.value, instrument):
            raise InvariantViolation(
                "SL and TP must not collapse to the same executable price tick"
            )

    # --- Public API -----------------------------------------------------------

    @staticmethod
    def validate(
        *,
        side: PositionSide,
        entry: Price | ReferencePrice,
        sl: Price | None,
        tp: Price | None,
        instrument: InstrumentSpec,
    ) -> None:
        """
        Validates Stop Loss / Take Profit constraints.

        Canonical rules:
        - Entry price is NEUTRAL (non-executable)
        - SL / TP are EXECUTABLE with directional safety
        - Ordering rules depend on PositionSide
        - SL and TP must remain distinct after quantization
        """

        q_entry = ExitPolicy._quantize_entry(
            entry=entry,
            instrument=instrument,
        )

        q_sl, q_tp = ExitPolicy._quantize_sl_tp(
            side=side,
            sl=sl,
            tp=tp,
            instrument=instrument,
        )

        if side.is_long():
            ExitPolicy._validate_long(
                entry=q_entry,
                sl=q_sl,
                tp=q_tp,
                instrument=instrument,
            )

        elif side.is_short():
            ExitPolicy._validate_short(
                entry=q_entry,
                sl=q_sl,
                tp=q_tp,
                instrument=instrument,
            )

        else:  # Defensive (should be unreachable)
            raise InvariantViolation(f"Unsupported PositionSide: {side}")

        if q_sl is not None and q_tp is not None:
            ExitPolicy._validate_distinct_sl_tp(
                sl=q_sl,
                tp=q_tp,
                instrument=instrument,
            )
