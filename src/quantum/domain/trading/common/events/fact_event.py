from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent


@dataclass(frozen=True, slots=True)
class FactEvent(BaseEvent, ABC):
    """
    Represents something that happened in reality.
    """
