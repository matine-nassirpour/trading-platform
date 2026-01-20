from __future__ import annotations

from typing import Protocol, runtime_checkable

from quantum.domain.trading.core.position.position import Position
from quantum.domain.trading.value_objects.identifiers.position_id import PositionId


@runtime_checkable
class PositionRepository(Protocol):
    """
    Persistence port for Position aggregate.
    """

    def get(self, position_id: PositionId) -> Position | None:
        raise NotImplementedError

    def save(self, position: Position) -> None:
        raise NotImplementedError
