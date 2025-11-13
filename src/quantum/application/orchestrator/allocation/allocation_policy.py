from __future__ import annotations

import secrets

from collections.abc import Sequence
from typing import Protocol

from quantum.domain.types.execution_channel import ExecutionChannel


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Base Protocol                                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
class AllocationPolicy(Protocol):
    """Abstract allocation policy for selecting execution channels."""

    def select_channel(
        self, available: Sequence[ExecutionChannel]
    ) -> ExecutionChannel: ...


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Round-robin                                                                │
# ╰────────────────────────────────────────────────────────────────────────────╯
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


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Random                                                                     │
# ╰────────────────────────────────────────────────────────────────────────────╯
class RandomAllocation(AllocationPolicy):
    """Random channel selection."""

    def select_channel(self, available: Sequence[ExecutionChannel]) -> ExecutionChannel:
        if not available:
            raise RuntimeError("No available execution channels")
        return secrets.choice(available)
