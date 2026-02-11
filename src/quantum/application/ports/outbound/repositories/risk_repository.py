from abc import abstractmethod
from typing import Protocol

from quantum.domain.risk.governance.aggregates.risk_state import RiskState


class RiskRepository(Protocol):

    @abstractmethod
    def load(self) -> RiskState:
        raise NotImplementedError

    @abstractmethod
    def save(self, state: RiskState) -> None:
        raise NotImplementedError
