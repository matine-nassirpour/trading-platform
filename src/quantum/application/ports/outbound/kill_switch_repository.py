from __future__ import annotations

from typing import Protocol, runtime_checkable

from quantum.domain.risk.governance.aggregates import KillSwitchState


@runtime_checkable
class KillSwitchRepository(Protocol):
    """
    Persistence port for KillSwitchState aggregate.

    Note:
    KillSwitchState is also naturally a singleton (global state).
    """

    def get_current(self) -> KillSwitchState | None:
        raise NotImplementedError

    def save(self, state: KillSwitchState) -> None:
        raise NotImplementedError
