from quantum.domain.model.exceptions.base import DomainError


class RiskError(DomainError):
    """Base class for risk-related domain errors."""


class DrawdownLimitExceeded(RiskError):
    """Raised when the maximum drawdown limit is exceeded."""


class InvalidDrawdownState(RiskError):
    """Raised when drawdown invariants are violated."""
