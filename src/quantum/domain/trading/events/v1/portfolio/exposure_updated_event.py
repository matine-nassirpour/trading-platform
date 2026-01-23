from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.money.notional import Notional
from quantum.domain.shared_kernel.value_objects.symbol import Symbol


@dataclass(frozen=True, slots=True)
class ExposureUpdatedEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.exposure.updated"
    event_version: ClassVar[int] = 1

    symbol: Symbol
    notional: Notional
