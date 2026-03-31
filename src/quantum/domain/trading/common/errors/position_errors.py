from quantum.domain.shared_kernel.foundation.errors.domain_error import DomainError


class PositionError(DomainError):
    """Base class for position-related domain errors."""


class PositionAlreadyClosed(PositionError):
    """Raised when attempting to close an already closed position."""


class InvalidPositionVolume(PositionError):
    """Raised when a position has an invalid volume."""


class InvalidEntryPrice(PositionError):
    """Raised when a position entry price is invalid."""
