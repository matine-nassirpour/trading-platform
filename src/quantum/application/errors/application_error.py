class ApplicationError(Exception):
    """
    Base class for all application-layer errors.

    Properties:
    - Represents a failure in application orchestration
    - NEVER raised by the domain layer
    - Mapped to infra-level errors (HTTP, RPC, logs, alerts)
    - Stable semantic contract
    """

    code: str = "application_error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.code)
