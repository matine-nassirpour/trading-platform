from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.trading.portfolio.balance import Balance


@dataclass(frozen=True, slots=True)
class BalanceUpdatedEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.balance.updated"
    event_version: ClassVar[int] = 1

    balance: Balance
