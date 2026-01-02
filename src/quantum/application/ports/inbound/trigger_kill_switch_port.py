from typing import Protocol

from quantum.application.dto.commands.trigger_kill_switch import (
    TriggerKillSwitchCommand,
)


class TriggerKillSwitchPort(Protocol):
    """
    Triggers the global trading kill switch.

    Responsibilities:
    - Validate transition rules
    - Update KillSwitchState aggregate
    - Emit KillSwitchTriggerEvent
    """

    def execute(self, command: TriggerKillSwitchCommand) -> None: ...
