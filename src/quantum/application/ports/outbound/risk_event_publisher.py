from abc import ABC, abstractmethod

from quantum.domain.risk.breaches.risk_breach import RiskBreach


class RiskEventPublisher(ABC):
    """
    Port for publishing risk breach notifications.
    """

    @abstractmethod
    def publish_breach(self, breach: RiskBreach) -> None:
        raise NotImplementedError
