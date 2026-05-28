from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent


@dataclass(frozen=True, slots=True)
class PositionSizingEvent(BaseEvent, ABC):
    """
    Represents an event related to position sizing.
    """
