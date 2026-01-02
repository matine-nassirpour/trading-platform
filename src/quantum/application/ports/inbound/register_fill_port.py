from typing import Protocol

from quantum.application.dto.commands.register_fill import RegisterFillCommand


class RegisterFillPort(Protocol):
    """
    Registers a fill on an existing Order.

    Responsibilities:
    - Load Order aggregate
    - Apply fill atomically
    - Persist updated Order
    - Emit fill-related domain events
    """

    def execute(self, command: RegisterFillCommand) -> None: ...
