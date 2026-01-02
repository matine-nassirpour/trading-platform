from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar


@dataclass(frozen=True)
class IntegrationEvent(ABC):
    event_name: ClassVar[str]
    event_version: ClassVar[int]
    occurred_at: datetime
