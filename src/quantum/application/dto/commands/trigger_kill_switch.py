from dataclasses import dataclass

from quantum.domain.risk.value_objects.kill_switch_reason import KillSwitchReason
from quantum.domain.shared_kernel.value_objects.epoch_ms import EpochMs


@dataclass(frozen=True)
class TriggerKillSwitchCommand:
    reason: KillSwitchReason
    at: EpochMs
    detail: str | None = None
