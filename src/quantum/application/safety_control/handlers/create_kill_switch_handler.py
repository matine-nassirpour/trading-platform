from collections.abc import Sequence

from quantum.application.safety_control.commands.create_kill_switch_command import (
    CreateKillSwitchCommand,
)
from quantum.application.safety_control.results.kill_switch_command_result import (
    CreateKillSwitchResult,
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


class CreateKillSwitchHandler(
    AggregateCommandHandler[
        CreateKillSwitchCommand,
        CreateKillSwitchResult,
        KillSwitchId,
        KillSwitchStateBase,
        KillSwitch,
    ]
):
    """
    Use case: create and arm a KillSwitch aggregate.

    Existence policy expected at composition root:
    - MUST_NOT_EXIST
    """

    def _aggregate_id(
        self,
        command: CreateKillSwitchCommand,
    ) -> KillSwitchId:
        return command.kill_switch_id

    def _context(
        self,
        command: CreateKillSwitchCommand,
    ) -> ApplicationEventContext:
        return command.context

    def _execute_domain(
        self,
        *,
        command: CreateKillSwitchCommand,
        aggregate: KillSwitch,
    ) -> tuple[Sequence[BaseEvent], CreateKillSwitchResult]:
        _, events = KillSwitch.create_new(aggregate_id=command.kill_switch_id)

        return events, CreateKillSwitchResult(
            kill_switch_id=command.kill_switch_id,
        )
