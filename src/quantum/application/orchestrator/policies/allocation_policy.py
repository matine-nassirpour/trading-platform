from __future__ import annotations

import secrets

from abc import ABC, abstractmethod
from collections.abc import Sequence

from quantum.domain.types.execution_channel import ExecutionChannel


class AllocationPolicy(ABC):
    """Abstract allocation policy for selecting execution channels."""

    @abstractmethod
    def select_channel(
        self, available: Sequence[ExecutionChannel]
    ) -> ExecutionChannel: ...


class RoundRobinAllocation(AllocationPolicy):
    """Deterministic round-robin allocation."""

    def __init__(self) -> None:
        self._index = 0

    def select_channel(self, available: Sequence[ExecutionChannel]) -> ExecutionChannel:
        if not available:
            raise RuntimeError("No available execution channels")
        channel = available[self._index % len(available)]
        self._index += 1
        return channel


class RandomAllocation(AllocationPolicy):
    """Random channel selection."""

    def select_channel(self, available: Sequence[ExecutionChannel]) -> ExecutionChannel:
        if not available:
            raise RuntimeError("No available execution channels")
        return secrets.choice(available)
