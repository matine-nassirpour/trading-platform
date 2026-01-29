from abc import ABC

from quantum.domain.shared_kernel.events.base.base_event import BaseEvent


class IntegrationEvent(BaseEvent, ABC):
    """
    Represents an event coming from or going to
    an external system.
    """
