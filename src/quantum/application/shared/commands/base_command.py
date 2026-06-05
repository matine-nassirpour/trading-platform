from dataclasses import dataclass

from quantum.application.shared.commands.command_id import CommandId
from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)


@dataclass(frozen=True, slots=True)
class BaseCommand:
    """
    Root class for all application commands.

    Guarantees:
    - Mandatory command identity
    - Mandatory causal context
    - Idempotent command processing support
    - Audit-grade traceability
    """

    command_id: CommandId
    context: ApplicationEventContext
