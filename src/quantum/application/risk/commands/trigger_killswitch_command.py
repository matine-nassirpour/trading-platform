from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.risk.kill_switch.reason import KillSwitchReason


@dataclass(frozen=True, slots=True)
class TriggerKillSwitchCommand(BaseCommand):
    reason: KillSwitchReason
    detail: str | None = None
