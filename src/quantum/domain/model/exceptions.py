class DomainError(Exception):
    """Base domain error."""


class InvalidStateTransition(DomainError):
    pass


class RiskViolation(DomainError):
    pass
