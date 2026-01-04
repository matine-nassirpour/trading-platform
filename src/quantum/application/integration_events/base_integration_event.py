from abc import ABC
from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class IntegrationEvent(ABC):
    event_name: ClassVar[str]
    event_version: ClassVar[int]
    occurred_at: EpochMs
