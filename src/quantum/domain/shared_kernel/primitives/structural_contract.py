from dataclasses import is_dataclass


class StructuralContractViolation(TypeError):
    """
    Raised when a domain primitive violates its structural contract.
    """


def _collect_all_slots(cls: type) -> set[str]:
    """
    Collects __slots__ from the full MRO.

    This is required because slots are not inherited automatically
    in Python unless explicitly re-declared.
    """
    slots: set[str] = set()

    for base in cls.__mro__:
        base_slots = getattr(base, "__slots__", None)
        if base_slots is None:
            continue

        if isinstance(base_slots, str):
            slots.add(base_slots)
        else:
            slots.update(base_slots)

    return slots


def _assert_no_forbidden_slots(cls: type) -> None:
    slots = _collect_all_slots(cls)

    if "__dict__" in slots:
        raise StructuralContractViolation(
            f"{cls.__name__} exposes __dict__ via __slots__. "
            "This violates immutability and memory guarantees."
        )

    if "__weakref__" in slots:
        raise StructuralContractViolation(
            f"{cls.__name__} exposes __weakref__. "
            "Weak references are forbidden for domain primitives."
        )


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
    - Must be immutable by construction
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
    if not params.frozen:
        raise StructuralContractViolation(
            f"{cls.__name__} must be declared with frozen=True"
        )

    # --- 3. Must use slots
    if not params.slots:
        raise StructuralContractViolation(
            f"{cls.__name__} must be declared with slots=True"
        )

    # --- 4. Slots must NOT expose __dict__ or __weakref__
    _assert_no_forbidden_slots(cls)

    # --- 5. Final sanity check (defensive)
    try:
        dummy = object.__new__(cls)
    except Exception:
        # Abstract classes may fail instantiation — that's fine
        return

    if hasattr(dummy, "__dict__"):
        raise StructuralContractViolation(
            f"{cls.__name__} instances expose __dict__, "
            "despite slots=True. This is forbidden."
        )
