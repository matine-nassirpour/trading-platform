from __future__ import annotations

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.temporal.epoch_ms import EpochMs


@runtime_checkable
class Clock(Protocol):
    """
    Deterministic time source for the application layer.
    """

    @abstractmethod
    def now_epoch_ms(self) -> EpochMs:
        raise NotImplementedError
