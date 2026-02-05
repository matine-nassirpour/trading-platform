from typing import Protocol, runtime_checkable

from quantum.domain.risk.governance.aggregates.risk_state import RiskState


@runtime_checkable
class RiskStateRepository(Protocol):
    """
    Persistence port for RiskState aggregate.

    Note:
    RiskState has no explicit ID in your domain. Therefore we model it as a singleton
    per "desk/account context" in infrastructure.
    """

    def load(self) -> RiskState:
        raise NotImplementedError

    def save(self, state: RiskState) -> None:
        raise NotImplementedError
