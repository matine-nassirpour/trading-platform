from quantum.domain.shared_kernel.foundation.errors.domain_error import DomainError


class ProjectionError(DomainError):
    """
    Raised when a projection encounters an unrecoverable inconsistency.
    """
