class DomainError(Exception):
    """
    Base class for all domain-level exceptions.

    Properties:
    - Semantic (business meaning)
    - Deterministic
    - Non-recoverable inside the domain
    """
