from dataclasses import dataclass

from quantum.domain.safety_control.kill_switch.kill_switch_detail import (
    KillSwitchDetail,
)
from quantum.domain.safety_control.kill_switch.kill_switch_id import KillSwitchId
from quantum.domain.safety_control.kill_switch.kill_switch_reason import (
    KillSwitchReason,
)


@dataclass(frozen=True, slots=True)
class KillSwitchCommandResult:
    """
    Base application result for commands targeting KillSwitch.
    """

    kill_switch_id: KillSwitchId


@dataclass(frozen=True, slots=True)
class CreateKillSwitchResult(KillSwitchCommandResult):
    """
    Result for kill-switch creation/arming workflow.
    """


@dataclass(frozen=True, slots=True)
class TriggerKillSwitchResult(KillSwitchCommandResult):
    """
    Result for kill-switch triggering workflow.
    """

    reason: KillSwitchReason
    detail: KillSwitchDetail | None
