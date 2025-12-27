class DomainError(Exception):
    """Base class for all domain-level errors."""


class InvariantViolation(DomainError):
    """Raised when a domain invariant is violated."""


class InvalidStateTransition(DomainError):
    """Raised on illegal aggregate state transitions."""


class RiskViolation(DomainError):
    """Raised when a risk constraint is breached."""
