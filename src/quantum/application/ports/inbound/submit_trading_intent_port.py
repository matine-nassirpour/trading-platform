from typing import Protocol

from quantum.application.dto.commands.submit_trading_intent import (
    SubmitTradingIntentCommand,
)


class SubmitTradingIntentPort(Protocol):
    """
    Submits a new trading intent into the system.

    Responsibilities:
    - Validate the intent at application level
    - Emit the corresponding domain events
    - Persist the TradingIntent aggregate

    This port is the canonical entry point
    for intent submission.
    """

    def execute(self, command: SubmitTradingIntentCommand) -> None: ...
