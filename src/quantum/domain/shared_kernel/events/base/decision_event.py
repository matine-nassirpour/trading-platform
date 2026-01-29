from abc import ABC

from quantum.domain.shared_kernel.events.base.base_event import BaseEvent


class DecisionEvent(BaseEvent, ABC):
    """
    Represents a deliberate decision made by the system.
    """
