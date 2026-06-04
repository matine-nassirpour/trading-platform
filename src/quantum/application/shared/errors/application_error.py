from quantum.domain.shared_kernel.foundation.errors.domain_error import DomainError


class ApplicationError(Exception):
    """
    Base class for all application-layer errors.
    """


class UseCaseError(ApplicationError):
    """
    Raised when a use case cannot be completed for business reasons.
    """


class NotFoundError(ApplicationError):
    """
    Raised when a required resource cannot be found.
    """


class ConcurrencyError(ApplicationError):
    """
    Raised on optimistic concurrency violation.
    """


class ValidationError(ApplicationError):
    """
    Raised when input validation fails before reaching the domain.
    """


class DomainExecutionError(ApplicationError):
    """
    Wraps a DomainError when crossing boundaries.
    """

    def __init__(self, error: DomainError):
        super().__init__(str(error))
        self.original_error = error


class AggregateNotFoundError(ApplicationError):
    """
    Raised when an expected aggregate does not exist in the event store.
    """

    def __init__(self, stream_id: str):
        super().__init__(f"Aggregate not found for stream '{stream_id}'")
        self.stream_id = stream_id


class EmptyDomainEventError(ApplicationError):
    """
    Raised when a mutating event-sourced command produced no domain events.
    """


class TooManyDomainEventsError(ApplicationError):
    """
    Raised when a command produces more domain events than allowed
    by application safety policy.
    """

    def __init__(
        self,
        *,
        command_name: str,
        produced: int,
        maximum: int,
    ) -> None:
        super().__init__(
            f"Command '{command_name}' produced {produced} domain events, "
            f"which exceeds the maximum allowed limit of {maximum}"
        )
        self.command_name = command_name
        self.produced = produced
        self.maximum = maximum


class ApplicationInvariantViolationError(ApplicationError):
    """
    Raised when an application-layer invariant is violated.
    """


class RepositoryIntegrityError(ApplicationError):
    """
    Raised when a repository detects corrupted, inconsistent,
    or contract-violating persistence data.
    """


class ProjectionConsistencyError(ApplicationError):
    """
    Raised when a projection detects cursor, ordering,
    idempotency, or consistency violation.
    """
