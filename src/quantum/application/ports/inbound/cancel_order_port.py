from typing import Protocol

from quantum.application.commands.cancel_order import CancelOrderCommand


class CancelOrderPort(Protocol):
    """
    Cancels an existing Order.

    Responsibilities:
    - Validate order state
    - Apply cancellation
    - Persist updated Order
    - Emit cancellation-related domain events
    """

    def execute(self, command: CancelOrderCommand) -> None: ...
