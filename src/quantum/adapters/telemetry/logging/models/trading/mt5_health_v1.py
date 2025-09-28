from typing import Literal

from quantum.adapters.telemetry.logging.models.trading.base import BaseEvent


class Mt5HealthV1(BaseEvent):
    event_name: Literal["mt5_health_v1"] = "mt5_health_v1"
    app: Literal["ea_mql5"]
    terminal_build: int
    account_login: int
    account_server: str
    account_currency: str
    leverage: int
    hedging: bool
    trade_allowed: bool
    connection_up: bool
    free_margin: float | None = None
    update_ms: int
