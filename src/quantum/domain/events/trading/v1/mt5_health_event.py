from dataclasses import dataclass
from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.model.value_objects.time import EpochMs
from quantum.domain.types.enums import App


@dataclass(frozen=True)
class Mt5HealthEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.mt5_health"
    terminal_build: int
    account_login: int
    account_server: str
    account_currency: str
    leverage: int
    hedging: bool
    trade_allowed: bool
    connection_up: bool
    update_epoch_ms: EpochMs
    app: App = App.EA_MQL5
    free_margin: float | None = None
