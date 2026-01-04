from abc import ABC
from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class BaseEvent(ABC):
    """
    Canonical immutable Domain Event.

    Guarantees:
    - Immutable
    - Versioned
    - Schema-introspectable
    """

    event_name: ClassVar[str]
    event_version: ClassVar[int] = 1
    occurred_at: EpochMs
