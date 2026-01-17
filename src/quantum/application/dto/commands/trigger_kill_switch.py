from dataclasses import dataclass

from quantum.domain.risk.governance.aggregates.kill_switch.reason import (
    KillSwitchReason,
)
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class TriggerKillSwitchCommand:
    reason: KillSwitchReason
    at: EpochMs
    detail: str | None = None
