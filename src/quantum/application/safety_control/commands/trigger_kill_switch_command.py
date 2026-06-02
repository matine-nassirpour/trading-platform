from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.safety_control.kill_switch.kill_switch_detail import (
    KillSwitchDetail,
)
from quantum.domain.safety_control.kill_switch.kill_switch_id import KillSwitchId
from quantum.domain.safety_control.kill_switch.kill_switch_reason import (
    KillSwitchReason,
)


@dataclass(frozen=True, slots=True)
class TriggerKillSwitchCommand(BaseCommand):
    """
    Command: trigger an armed KillSwitch.

    Domain consequence:
    - KillSwitchTriggeredEvent
    """

    kill_switch_id: KillSwitchId
    reason: KillSwitchReason
    detail: KillSwitchDetail | None = None
