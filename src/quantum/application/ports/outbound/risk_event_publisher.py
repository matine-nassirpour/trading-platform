from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.risk.breaches.risk_breach import RiskBreach


@runtime_checkable
class RiskEventPublisher(Protocol):
    """
    Port for publishing risk breach notifications.
    """

    @abstractmethod
    def publish_breach(self, breach: RiskBreach) -> None:
        raise NotImplementedError
