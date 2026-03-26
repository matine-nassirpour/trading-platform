from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN
from typing import Final

from quantum.domain.market.positioning.position_side import PositionSide
from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.trading.execution.pricing.pricing_context import PricingContext


class _RoundingStrategy:
    """
    INTERNAL pricing rounding strategy.

    This class MUST NOT be used directly outside PricingPolicy.
    It encapsulates all directional rounding rules.
    """

    NEUTRAL: Final[str] = ROUND_HALF_EVEN

    @staticmethod
    def execution(
        *,
        context: PricingContext,
        side: PositionSide,
    ) -> str:
        if context.is_execution_sl():
            return ROUND_FLOOR if side.is_long() else ROUND_CEILING

        if context.is_execution_tp():
            return ROUND_CEILING if side.is_long() else ROUND_FLOOR

        raise InvariantViolation(f"Unsupported execution pricing context: {context}")
