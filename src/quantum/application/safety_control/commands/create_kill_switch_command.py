from dataclasses import dataclass

from quantum.application.shared.commands.base_command import BaseCommand
from quantum.domain.safety_control.kill_switch.kill_switch_id import KillSwitchId


@dataclass(frozen=True, slots=True)
class CreateKillSwitchCommand(BaseCommand):
    """
    Command: create and arm a KillSwitch aggregate stream.

    Domain consequence:
    - KillSwitchArmedEvent
    """

    kill_switch_id: KillSwitchId
