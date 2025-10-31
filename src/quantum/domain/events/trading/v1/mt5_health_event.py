from typing import ClassVar

from quantum.domain.events.base import BaseEvent
from quantum.domain.serialization import register_event
from quantum.domain.types.enums import App
from quantum.domain.value_objects import EpochMs


@register_event
class Mt5HealthEvent(BaseEvent):
    event_name: ClassVar[str] = "trading.mt5_health"
    app: App = App.EA_MQL5
    terminal_build: int
    account_login: int
    account_server: str
    account_currency: str
    leverage: int
    hedging: bool
    trade_allowed: bool
    connection_up: bool
    free_margin: float | None = None
    update_epoch_ms: EpochMs
