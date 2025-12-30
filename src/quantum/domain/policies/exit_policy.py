from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.instrument_spec import InstrumentSpec
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.reference_price import ReferencePrice
from quantum.domain.policies.exit_pricing_policy import ExitPricingPolicy
from quantum.domain.policies.pricing_policy import PricingPolicy
from quantum.domain.types.position_side import PositionSide


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
        It uses neutral (statistical) quantization.
        """
        quantized = PricingPolicy.quantize_price(entry.value, instrument)
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
        Applies directional, executable quantization to SL / TP.
        """
        q_sl = (
            Price(
                ExitPricingPolicy.quantize_sl(
                    value=sl.value,
                    side=side,
                    instrument=instrument,
                )
            )
            if sl
            else None
        )

        q_tp = (
            Price(
                ExitPricingPolicy.quantize_tp(
                    value=tp.value,
                    side=side,
                    instrument=instrument,
                )
            )
            if tp
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
        - Entry price is neutrally quantized (non-executable)
        - SL / TP are directionally quantized (executable)
        - All comparisons use quantized values
        - Ordering depends on PositionSide
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

        if side == PositionSide.LONG:
            ExitPolicy._validate_long(
                entry=q_entry,
                sl=q_sl,
                tp=q_tp,
                instrument=instrument,
            )

        elif side == PositionSide.SHORT:
            ExitPolicy._validate_short(
                entry=q_entry,
                sl=q_sl,
                tp=q_tp,
                instrument=instrument,
            )

        else:
            raise InvariantViolation(f"Unsupported PositionSide: {side}")

        if q_sl and q_tp:
            ExitPolicy._validate_distinct_sl_tp(
                sl=q_sl,
                tp=q_tp,
                instrument=instrument,
            )
