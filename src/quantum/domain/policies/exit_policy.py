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
        entry_price,
        sl: Price | None,
        tp: Price | None,
    ) -> None:
        if sl and sl.value >= entry_price:
            raise InvariantViolation("LONG position requires SL < entry price")

        if tp and tp.value <= entry_price:
            raise InvariantViolation("LONG position requires TP > entry price")

    @staticmethod
    def _validate_short(
        entry_price,
        sl: Price | None,
        tp: Price | None,
    ) -> None:
        if sl and sl.value <= entry_price:
            raise InvariantViolation("SHORT position requires SL > entry price")

        if tp and tp.value >= entry_price:
            raise InvariantViolation("SHORT position requires TP < entry price")

    @staticmethod
    def _validate_distinct_sl_tp(
        sl: Price | None,
        tp: Price | None,
        instrument: InstrumentSpec,
    ) -> None:
        if sl and tp:
            if PricingPolicy.price_equal(sl.value, tp.value, instrument):
                raise InvariantViolation("SL and TP must be distinct")

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
        entry_price = entry.value

        if side == PositionSide.LONG:
            ExitPolicy._validate_long(entry_price, sl, tp)

        elif side == PositionSide.SHORT:
            ExitPolicy._validate_short(entry_price, sl, tp)

        else:
            raise InvariantViolation(f"Unsupported PositionSide: {side}")

        if sl and tp:
            ExitPolicy._validate_distinct_sl_tp(sl, tp, instrument)
