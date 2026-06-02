from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.position_sizing.position_sizing_id import PositionSizingId


@dataclass(frozen=True, slots=True)
class PerformPositionSizingCommand(BaseCommand):
    """
    Command: perform sizing for a pending PositionSizing aggregate.

    The domain may emit either:
    - PositionSizedEvent
    - PositionSizingRejectedEvent
    """

    sizing_id: PositionSizingId
