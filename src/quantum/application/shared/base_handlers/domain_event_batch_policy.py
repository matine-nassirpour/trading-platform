from dataclasses import dataclass

from quantum.application.shared.errors.application_error import TooManyDomainEventsError
from quantum.domain.shared_kernel.event_sourcing.events.base_event import BaseEvent


@dataclass(frozen=True, slots=True)
class DomainEventBatchPolicy:
    """
    Application-level safety policy limiting the number of domain events
    produced by a single aggregate command.

    Rationale:
    - preserve transactional boundedness
    - prevent memory explosion
    - prevent oversized event-store append operations
    - enforce command granularity
    """

    max_events_per_command: int = 256

    def validate(
        self,
        *,
        command_name: str,
        events: list[BaseEvent],
    ) -> None:
        produced = len(events)

        if produced > self.max_events_per_command:
            raise TooManyDomainEventsError(
                command_name=command_name,
                produced=produced,
                maximum=self.max_events_per_command,
            )
