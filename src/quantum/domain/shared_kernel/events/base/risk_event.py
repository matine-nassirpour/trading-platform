from abc import ABC

from quantum.domain.shared_kernel.events.base.base_event import BaseEvent


class RiskEvent(BaseEvent, ABC):
    """
    Represents an event related to risk management,
    capital protection, or system safety.
    """
