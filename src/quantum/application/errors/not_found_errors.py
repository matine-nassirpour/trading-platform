from quantum.application.errors.application_error import ApplicationError


class NotFoundError(ApplicationError):
    """
    Base class for missing aggregate/entity errors.
    """

    code = "not_found"


class TradingIntentNotFound(NotFoundError):
    code = "trading_intent_not_found"

    def __init__(self, intent_id) -> None:
        super().__init__(f"TradingIntent not found: {intent_id}")


class OrderNotFound(NotFoundError):
    code = "order_not_found"

    def __init__(self, order_id) -> None:
        super().__init__(f"Order not found: {order_id}")


class PositionNotFound(NotFoundError):
    code = "position_not_found"

    def __init__(self, position_id) -> None:
        super().__init__(f"Position not found: {position_id}")
