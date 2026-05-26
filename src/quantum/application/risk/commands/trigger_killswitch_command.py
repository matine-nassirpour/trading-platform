from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.safety_control.kill_switch.kill_switch_reason import (
    KillSwitchReason,
)


@dataclass(frozen=True, slots=True)
class TriggerKillSwitchCommand(BaseCommand):
    reason: KillSwitchReason
    detail: str | None = None
