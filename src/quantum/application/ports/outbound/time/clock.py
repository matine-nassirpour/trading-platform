from typing import Protocol, runtime_checkable

from quantum.domain.shared_kernel.modeling.temporal.epoch_ms import EpochMs


@runtime_checkable
class Clock(Protocol):
    """
    Deterministic time source for the application layer.
    """

    def now_epoch_ms(self) -> EpochMs: ...
