from __future__ import annotations

from quantum.domain.model.exceptions.validation_exceptions import InvariantViolation
from quantum.domain.model.value_objects.order_request_snapshot import (
    OrderRequestSnapshot,
)
from quantum.domain.types.enums import OrderType


class ExecutionValidationService:
    """
    Domain Service responsible for validating order execution semantics.
    """

    @staticmethod
    def validate_order_request(request: OrderRequestSnapshot) -> None:
        """
        Validates cross-field order coherence.

        Rules:
        - Market orders must not define price
        - Pending orders must define price
        - SL / TP must not equal entry price
        """

        order_type = request.order_type

        # Price coherence
        if order_type in {OrderType.BUY, OrderType.SELL}:
            if request.price is not None:
                raise InvariantViolation("Market orders must not define an entry price")
        else:
            if request.price is None:
                raise InvariantViolation("Pending orders must define an entry price")

        # SL / TP coherence
        if request.sl and request.price and request.sl.value == request.price.value:
            raise InvariantViolation("Stop loss cannot equal entry price")

        if request.tp and request.price and request.tp.value == request.price.value:
            raise InvariantViolation("Take profit cannot equal entry price")
