from abc import ABC

from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent


class DecisionEvent(BaseEvent, ABC):
    """
    Represents a deliberate decision made by the system.
    """
