from collections.abc import Iterable
from dataclasses import is_dataclass
from typing import Protocol, cast


class StructuralContractViolation(TypeError):
    """
    Raised when a domain primitive violates its structural contract.
    """


class _DataclassParamsProtocol(Protocol):
    frozen: bool
    slots: bool


# ------------------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------------------
def _get_dataclass_params(cls: type) -> _DataclassParamsProtocol:
    params = getattr(cls, "__dataclass_params__", None)
    if params is None:
        raise StructuralContractViolation(f"{cls.__name__} must be a dataclass")
    return cast(_DataclassParamsProtocol, params)


def _get_slots(cls: type) -> Iterable[str]:
    slots = cls.__dict__.get("__slots__")

    if slots is None:
        raise StructuralContractViolation(f"{cls.__name__} must define __slots__")

    if isinstance(slots, str):
        return (slots,)

    return tuple(slots)


# ------------------------------------------------------------------------------
# Public contract
# ------------------------------------------------------------------------------
def enforce_frozen_slot_dataclass_contract(cls: type) -> None:
    """
    Enforces the canonical structural contract for all immutable
    domain primitives.

    HARD GUARANTEES:
    - Must be a dataclass
    - Must be frozen
    - Must use __slots__
    - Must not have __dict__
    - Must not have __weakref__
    """

    # Must be dataclass
    if not is_dataclass(cls):
        raise StructuralContractViolation(f"{cls.__name__} must be a dataclass")

    params = _get_dataclass_params(cls)

    # Must be frozen
    if not params.frozen:
        raise StructuralContractViolation(f"{cls.__name__} must be frozen=True")

    # Must use slots
    if not params.slots:
        raise StructuralContractViolation(f"{cls.__name__} must be slots=True")

    # Must not expose __dict__ or __weakref__
    slots = _get_slots(cls)

    if "__dict__" in slots:
        raise StructuralContractViolation(
            f"{cls.__name__} must not include '__dict__' in __slots__"
        )

    if "__weakref__" in slots:
        raise StructuralContractViolation(
            f"{cls.__name__} must not include '__weakref__' in __slots__"
        )
