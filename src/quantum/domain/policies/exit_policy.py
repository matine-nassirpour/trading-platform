from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.instrument_spec import InstrumentSpec
from quantum.domain.model.value_objects.price import Price
from quantum.domain.model.value_objects.reference_price import ReferencePrice
from quantum.domain.policies.pricing_policy import PricingPolicy
from quantum.domain.types.position_side import PositionSide


class ExitPolicy:
    """
    Canonical SL/TP validation policy.

    Contextual:
    - side (LONG / SHORT)
    - entry or reference price
    - instrument specification
    """

    # --- Internal Helpers -----------------------------------------------------

    @staticmethod
    def _validate_long(
        *,
        entry_price,
        sl: Price | None,
        tp: Price | None,
        instrument: InstrumentSpec,
    ) -> None:
        if sl and not PricingPolicy.price_less_than(sl.value, entry_price, instrument):
            raise InvariantViolation(
                "LONG position requires SL strictly below entry price "
                "after price quantization"
            )

        if tp and not PricingPolicy.price_greater_than(
            tp.value, entry_price, instrument
        ):
            raise InvariantViolation(
                "LONG position requires TP strictly above entry price "
                "after price quantization"
            )

    @staticmethod
    def _validate_short(
        *,
        entry_price,
        sl: Price | None,
        tp: Price | None,
        instrument: InstrumentSpec,
    ) -> None:
        if sl and not PricingPolicy.price_greater_than(
            sl.value, entry_price, instrument
        ):
            raise InvariantViolation(
                "SHORT position requires SL strictly above entry price "
                "after price quantization"
            )

        if tp and not PricingPolicy.price_less_than(tp.value, entry_price, instrument):
            raise InvariantViolation(
                "SHORT position requires TP strictly below entry price "
                "after price quantization"
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
                "SL and TP must be distinct after price quantization"
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
        - All comparisons are quantized
        - SL/TP ordering depends on position side
        - SL and TP must not collapse to the same tick
        """

        entry_price = entry.value

        if side == PositionSide.LONG:
            ExitPolicy._validate_long(
                entry_price=entry_price,
                sl=sl,
                tp=tp,
                instrument=instrument,
            )

        elif side == PositionSide.SHORT:
            ExitPolicy._validate_short(
                entry_price=entry_price,
                sl=sl,
                tp=tp,
                instrument=instrument,
            )

        else:
            raise InvariantViolation(f"Unsupported PositionSide: {side}")

        if sl and tp:
            ExitPolicy._validate_distinct_sl_tp(
                sl=sl,
                tp=tp,
                instrument=instrument,
            )
