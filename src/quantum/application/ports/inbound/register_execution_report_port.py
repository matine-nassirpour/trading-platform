from typing import Protocol

from quantum.application.dto.commands.register_execution_report import (
    RegisterExecutionReportCommand,
)


class RegisterExecutionReportPort(Protocol):
    """
    Registers an execution report coming from an execution venue.

    Responsibilities:
    - Validate execution report semantics
    - Update corresponding aggregates if needed
    - Emit execution-related domain events
    """

    def execute(self, command: RegisterExecutionReportCommand) -> None: ...
