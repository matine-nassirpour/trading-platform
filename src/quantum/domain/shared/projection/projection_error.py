from quantum.domain.shared.errors.domain_error import DomainError


class ProjectionError(DomainError):
    """
    Raised when a projection encounters an unrecoverable inconsistency.
    """
