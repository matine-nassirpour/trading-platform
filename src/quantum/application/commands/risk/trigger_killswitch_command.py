from dataclasses import dataclass

from quantum.domain.risk.governance.aggregates.kill_switch.reason import (
    KillSwitchReason,
)


@dataclass(frozen=True, slots=True)
class TriggerKillSwitchCommand:
    reason: KillSwitchReason
    detail: str | None = None
