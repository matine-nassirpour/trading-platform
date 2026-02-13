from abc import ABC
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class IntegrationEvent(ABC):
    """
    Pure application-level integration event.
    """

    event_name: ClassVar[str]
    event_version: ClassVar[int] = 1
