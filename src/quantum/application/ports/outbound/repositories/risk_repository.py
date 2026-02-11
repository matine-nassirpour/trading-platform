from abc import ABC, abstractmethod

from quantum.domain.risk.governance.aggregates.risk_state import RiskState


class RiskRepository(ABC):

    @abstractmethod
    def load(self) -> RiskState:
        raise NotImplementedError

    @abstractmethod
    def save(self, state: RiskState) -> None:
        raise NotImplementedError
