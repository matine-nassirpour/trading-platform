from quantum.domain.shared_kernel.foundation.errors.domain_error import DomainError


class RiskError(DomainError):
    """Base class for risk-related domain errors."""


class DrawdownLimitExceeded(RiskError):
    """Raised when the maximum drawdown limit is exceeded."""


class InvalidDrawdownState(RiskError):
    """Raised when drawdown invariants are violated."""
