from typing import Literal

from quantum.foundation.events.common.base import BaseEvent


class KillSwitchTriggerV1(BaseEvent):
    event_name: Literal["killswitch_trigger_v1"] = "killswitch_trigger_v1"
    app: Literal["ea_mql5"]
    trigger_ms: int
    reason: Literal["risk_limit", "network", "broker_rejects", "manual"]
    detail: str | None = None
