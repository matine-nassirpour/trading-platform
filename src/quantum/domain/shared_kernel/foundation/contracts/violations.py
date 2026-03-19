class StructuralContractViolation(TypeError):
    """
    Raised when a domain object violates a structural policy.

    IMPORTANT:
    This is NOT a domain semantic error.
    It is a programming / architecture violation detected at construction time.
    """
