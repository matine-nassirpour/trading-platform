from collections.abc import Sequence

from quantum.application.safety_control.commands.trigger_kill_switch_command import (
    TriggerKillSwitchCommand,
)
from quantum.application.safety_control.results.kill_switch_command_result import (
    TriggerKillSwitchResult,
)
from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)
from quantum.domain.safety_control.kill_switch.aggregate import KillSwitch
from quantum.domain.safety_control.kill_switch.kill_switch_id import KillSwitchId
from quantum.domain.safety_control.kill_switch.states.kill_switch_state_base import (
    KillSwitchStateBase,
)
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent


class TriggerKillSwitchHandler(
    AggregateCommandHandler[
        TriggerKillSwitchCommand,
        TriggerKillSwitchResult,
        KillSwitchId,
        KillSwitchStateBase,
        KillSwitch,
    ]
):
    """
    Use case: trigger an armed KillSwitch.

    Existence policy expected at composition root:
    - MUST_EXIST
    """

    def _aggregate_id(
        self,
        command: TriggerKillSwitchCommand,
    ) -> KillSwitchId:
        return command.kill_switch_id

    def _context(
        self,
        command: TriggerKillSwitchCommand,
    ) -> ApplicationEventContext:
        return command.context

    async def _execute_domain(
        self,
        *,
        command: TriggerKillSwitchCommand,
        aggregate: KillSwitch,
    ) -> tuple[Sequence[BaseEvent], TriggerKillSwitchResult]:
        events = aggregate.trigger(
            reason=command.reason,
            detail=command.detail,
        )

        return events, TriggerKillSwitchResult(
            kill_switch_id=command.kill_switch_id,
            reason=command.reason,
            detail=command.detail,
        )
