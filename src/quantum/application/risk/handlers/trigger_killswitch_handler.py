from collections.abc import Iterable

from quantum.application.risk.commands.trigger_killswitch_command import (
    TriggerKillSwitchCommand,
)
from quantum.application.shared.base_handlers.aggregate_command_handler import (
    AggregateCommandHandler,
)
from quantum.application.shared.base_handlers.aggregate_existence_policy import (
    AggregateExistencePolicy,
)
from quantum.domain.safety_control.aggregate import KillSwitch
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent


class TriggerKillSwitchHandler(
    AggregateCommandHandler[TriggerKillSwitchCommand, None, KillSwitch]
):
    """
    Triggers the global Kill Switch.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(
            existence_policy=AggregateExistencePolicy.MUST_EXIST,
            **kwargs,
        )

    def _stream_id(self, command: TriggerKillSwitchCommand) -> str:
        return "killswitch"

    def _execute_domain(
        self,
        *,
        command: TriggerKillSwitchCommand,
        aggregate: KillSwitch | None,
    ) -> tuple[Iterable[BaseEvent], None]:

        if aggregate is None:
            raise RuntimeError(
                "KillSwitchState aggregate missing despite MUST_EXIST policy enforcement."
            )

        domain_events = aggregate.trigger(
            reason=command.reason,
            detail=command.detail,
        )

        return domain_events, None
