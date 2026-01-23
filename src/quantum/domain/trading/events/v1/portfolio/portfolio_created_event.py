from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.shared_kernel.events.base_event import BaseEvent
from quantum.domain.shared_kernel.money.money_context import MoneyContext
from quantum.domain.trading.portfolio.account_id import AccountId


@dataclass(frozen=True, slots=True)
class PortfolioCreatedEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.portfolio.created"
    event_version: ClassVar[int] = 1

    account_id: AccountId
    context: MoneyContext
