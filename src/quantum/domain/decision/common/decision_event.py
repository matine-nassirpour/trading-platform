from abc import ABC
from dataclasses import dataclass

from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent


@dataclass(frozen=True, slots=True)
class DecisionEvent(BaseEvent, ABC):
    """
    Represents a deliberate decision made by the system.
    """
