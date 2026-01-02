from typing import Protocol

from quantum.application.dto.commands.create_order_from_intent import (
    CreateOrderFromIntentCommand,
)


class CreateOrderFromIntentPort(Protocol):
    """
    Creates an Order inside an already submitted TradingIntent.

    Responsibilities:
    - Load TradingIntent aggregate
    - Validate creation rules
    - Persist updated aggregate
    - Emit order-related domain events
    """

    def execute(self, command: CreateOrderFromIntentCommand) -> None: ...
