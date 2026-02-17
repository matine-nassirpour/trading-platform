from dataclasses import dataclass

from quantum.application.shared.eventing.application_event_context import (
    ApplicationEventContext,
)


@dataclass(frozen=True, slots=True)
class BaseCommand:
    """
    Root class for all application commands.

    Guarantees:
    - Mandatory causal context
    - Audit-grade traceability
    - DRY compliance
    """

    context: ApplicationEventContext
