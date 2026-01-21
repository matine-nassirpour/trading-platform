from dataclasses import is_dataclass


class StructuralContractViolation(TypeError):
    """
    Raised when a domain primitive violates its structural contract.
    """


# ------------------------------------------------------------------------------
# Public contract
# ------------------------------------------------------------------------------
def enforce_frozen_slot_dataclass_contract(cls: type) -> None:
    """
    Enforces the canonical structural contract for domain primitives.

    HARD GUARANTEES:
    - Must be a dataclass
    - Must be frozen
    - Must use slots=True
    - Must NOT expose __dict__
    - Must NOT expose __weakref__
    """

    # --- 1. Must be dataclass
    if not is_dataclass(cls):
        raise StructuralContractViolation(f"{cls.__name__} must be a dataclass")

    params = getattr(cls, "__dataclass_params__", None)
    if params is None:
        raise StructuralContractViolation(
            f"{cls.__name__} is missing __dataclass_params__"
        )

    # --- 2. Must be frozen
    if not getattr(params, "frozen", False):
        raise StructuralContractViolation(
            f"{cls.__name__} must be declared with frozen=True"
        )

    # --- 3. Must use slots
    if not getattr(params, "slots", False):
        raise StructuralContractViolation(
            f"{cls.__name__} must be declared with slots=True"
        )

    # --- 4. Must NOT expose __dict__
    if hasattr(cls, "__dict__"):
        raise StructuralContractViolation(
            f"{cls.__name__} exposes __dict__. " f"Slots enforcement is broken."
        )

    # --- 5. Must NOT expose __weakref__
    if hasattr(cls, "__weakref__"):
        raise StructuralContractViolation(
            f"{cls.__name__} exposes __weakref__. "
            f"This violates immutability guarantees."
        )
