from quantum.domain.model.exceptions.base import DomainError


class InvariantViolation(DomainError):
    """Raised when a domain invariant is violated."""


class InvalidStateTransition(DomainError):
    """Raised when an illegal state transition is attempted."""


class CurrencyMismatch(DomainError):
    """Raised when monetary currencies are incompatible."""
