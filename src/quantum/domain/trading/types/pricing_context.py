from enum import StrEnum


class PricingContext(StrEnum):
    """
    Canonical pricing context.

    Defines WHY a price is quantized, not HOW.
    This context drives rounding direction and safety rules.
    """

    NEUTRAL = "neutral"  # non-executable, statistical
    EXECUTION_SL = "execution_sl"  # worst-case rounding
    EXECUTION_TP = "execution_tp"  # best-case rounding
