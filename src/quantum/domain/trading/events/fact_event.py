from abc import ABC

from quantum.domain.shared_kernel.events.base.base_event import BaseEvent


class FactEvent(BaseEvent, ABC):
    """
    Represents something that happened in reality.
    """
