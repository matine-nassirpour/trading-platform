from collections.abc import Iterable

from quantum.application.commands.risk.trigger_killswitch_command import (
    TriggerKillSwitchCommand,
)
from quantum.application.handlers.base.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.domain.risk.governance.aggregates.kill_switch.state import KillSwitchState
from quantum.domain.shared_kernel.events.base.base_event import BaseEvent


class TriggerKillSwitchHandler(
    AggregateCommandHandler[TriggerKillSwitchCommand, None, KillSwitchState]
):
    """
    Triggers the global Kill Switch.
    """

    def _stream_id(self, command: TriggerKillSwitchCommand) -> str:
        return "killswitch"

    def _execute_domain(
        self,
        *,
        command: TriggerKillSwitchCommand,
        aggregate: KillSwitchState,
    ) -> tuple[Iterable[BaseEvent], None]:

        domain_events = aggregate.trigger(
            reason=command.reason,
            detail=command.detail,
        )

        return domain_events, None
