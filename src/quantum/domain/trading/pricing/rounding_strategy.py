from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN
from typing import Final

from quantum.domain.shared_kernel.foundation.errors.invariants import InvariantViolation
from quantum.domain.shared_kernel.modeling.services.domain_service import DomainService
from quantum.domain.trading.common.value_objects.position_side import PositionSide
from quantum.domain.trading.pricing.pricing_context import PricingContext


class _RoundingStrategy(DomainService):
    """
    INTERNAL pricing rounding strategy.

    This class MUST NOT be used directly outside PricingPolicy.
    It encapsulates all directional rounding rules.
    """

    __slots__ = ()

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
