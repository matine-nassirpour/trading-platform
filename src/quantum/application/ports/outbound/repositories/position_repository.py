from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.identifiers.position_id import PositionId
from quantum.domain.trading.execution.position.position import Position


@runtime_checkable
class PositionRepository(Protocol):
    """
    Persistence port for Position aggregate.
    """

    def load(self, position_id: PositionId) -> Position:
        raise NotImplementedError

    def save(self, position: Position) -> None:
        raise NotImplementedError
