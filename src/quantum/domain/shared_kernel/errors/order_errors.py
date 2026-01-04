from quantum.domain.shared_kernel.errors.domain_error import DomainError


class OrderError(DomainError):
    """Base class for order-related domain errors."""


class OrderNotFound(OrderError):
    """Raised when an order cannot be found in an aggregate."""


class OrderAlreadyAcknowledged(OrderError):
    """Raised when attempting to acknowledge an already acknowledged order."""


class OrderNotFillable(OrderError):
    """Raised when an order cannot accept fills in its current state."""


class OrderOverfill(OrderError):
    """Raised when a fill exceeds the requested volume."""
