from typing import Protocol

from quantum.application.commands.close_position import ClosePositionCommand


class ClosePositionPort(Protocol):
    """
    Closes an open trading position.

    Responsibilities:
    - Load Position aggregate
    - Compute realized PnL
    - Persist closed Position
    """

    def execute(self, command: ClosePositionCommand) -> None: ...
