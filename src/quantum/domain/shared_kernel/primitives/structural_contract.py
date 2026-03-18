import inspect

from dataclasses import fields, is_dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from functools import cache
from types import MappingProxyType
from typing import Any
from uuid import UUID

_ALLOWED_DEEPLY_IMMUTABLE_SCALARS = (
    str,
    int,
    bool,
    Decimal,
    UUID,
    date,
    time,
    timedelta,
    timezone,
    type(None),
)


class StructuralContractViolation(TypeError):
    """
    Raised when a domain primitive violates its structural contract.
    """


# --- Internal Helpers ---------------------------------------------------------


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
            "This violates the structural immutability contract."
        )

    if "__weakref__" in slots:
        raise StructuralContractViolation(
            f"{cls.__name__} exposes __weakref__. "
            "Weak references are forbidden in domain primitives."
        )


def _is_frozen_slotted_dataclass_class(cls: type) -> bool:
    if not is_dataclass(cls):
        return False

    params = getattr(cls, "__dataclass_params__", None)
    if not params or not getattr(params, "frozen", False):
        return False

    if not hasattr(cls, "__slots__"):
        return False

    try:
        dummy = object.__new__(cls)
    except Exception:
        # Defensive: if object creation is impossible, we still rely on class-level checks
        return True

    return not hasattr(dummy, "__dict__")


def _validate_datetime_is_deterministic(value: datetime, path: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise StructuralContractViolation(
            f"{path} must be timezone-aware; naive datetime is forbidden"
        )


def _assert_not_forbidden_mutable_type(value: Any, path: str) -> None:
    if isinstance(value, float):
        raise StructuralContractViolation(
            f"{path} uses float, which is forbidden in domain primitives; "
            "use Decimal or an explicit ValueObject"
        )

    if isinstance(value, (list, dict, set, bytearray)):
        raise StructuralContractViolation(
            f"{path} contains unsupported mutable value of type {type(value).__name__}"
        )


def _assert_tuple_is_deeply_immutable(value: tuple[Any, ...], path: str) -> None:
    for index, item in enumerate(value):
        _assert_deeply_immutable_value(item, f"{path}[{index}]")


def _assert_frozenset_is_deeply_immutable(value: frozenset[Any], path: str) -> None:
    for item in value:
        _assert_deeply_immutable_value(item, f"{path}[{item!r}]")


def _assert_mapping_proxy_is_deeply_immutable(
    value: MappingProxyType, path: str
) -> None:
    for key, item in value.items():
        if not isinstance(key, str):
            raise StructuralContractViolation(
                f"{path} contains non-string mapping key {key!r}; "
                "only MappingProxyType[str, deeply immutable] is allowed"
            )
        _assert_deeply_immutable_value(item, f"{path}[{key!r}]")


def _assert_dataclass_instance_is_deeply_immutable(value: Any, path: str) -> None:
    cls = type(value)

    if not _is_frozen_slotted_dataclass_class(cls):
        raise StructuralContractViolation(
            f"{path} contains dataclass {cls.__name__} which is not " "frozen + slotted"
        )

    for f in fields(value):
        _assert_deeply_immutable_value(
            getattr(value, f.name),
            f"{path}.{f.name}",
        )


def _assert_deeply_immutable_value(value: Any, path: str) -> None:
    """
    Recursively enforces the deep immutability contract for domain primitives.

    Allowed:
    - None
    - bool
    - int
    - str
    - Decimal
    - UUID
    - date
    - time
    - timedelta
    - timezone-aware datetime
    - Enum
    - tuple[deeply immutable]
    - frozenset[deeply immutable]
    - MappingProxyType[str, deeply immutable]
    - frozen, slotted dataclass instances whose fields are themselves deeply immutable

    Forbidden:
    - float
    - list
    - dict
    - set
    - bytearray
    - mutable dataclasses
    - arbitrary objects exposing mutable state
    """

    if isinstance(value, _ALLOWED_DEEPLY_IMMUTABLE_SCALARS):
        return

    if isinstance(value, datetime):
        _validate_datetime_is_deterministic(value, path)
        return

    _assert_not_forbidden_mutable_type(value, path)

    if isinstance(value, Enum):
        return

    if isinstance(value, tuple):
        _assert_tuple_is_deeply_immutable(value, path)
        return

    if isinstance(value, frozenset):
        _assert_frozenset_is_deeply_immutable(value, path)
        return

    if isinstance(value, MappingProxyType):
        _assert_mapping_proxy_is_deeply_immutable(value, path)
        return

    if is_dataclass(value):
        _assert_dataclass_instance_is_deeply_immutable(value, path)
        return

    raise StructuralContractViolation(
        f"{path} contains unsupported mutable or non-deterministic value "
        f"of type {type(value).__name__}"
    )


def _assert_deep_immutability_of_instance_fields(instance: object) -> None:
    """
    Validates every dataclass field of an instance against the deep immutability contract.
    """
    for f in fields(instance):
        _assert_deeply_immutable_value(
            getattr(instance, f.name),
            f"{type(instance).__name__}.{f.name}",
        )


# --- Public contract ----------------------------------------------------------


@cache
def _validate_structural_contract(cls: type) -> None:
    """
    Enforces the canonical structural contract for domain primitives.

    HARD GUARANTEES:
    - Must be a dataclass
    - Must be frozen
    - Must expose a slots-only instance layout
    - Must NOT expose __dict__
    - Must NOT expose __weakref__
    - Deep immutability is validated at instance construction time
    """

    # --- 1. Ignore abstract base classes ---
    if inspect.isabstract(cls):
        return

    # --- 2. Must be dataclass
    if not is_dataclass(cls):
        raise StructuralContractViolation(f"{cls.__name__} must be a dataclass")

    # --- 3. Must be frozen
    params = getattr(cls, "__dataclass_params__", None)
    if not params or not getattr(params, "frozen", False):
        raise StructuralContractViolation(
            f"{cls.__name__} must be declared with frozen=True"
        )

    # --- 4. Must use slots (robust check)
    if not hasattr(cls, "__slots__"):
        raise StructuralContractViolation(
            f"{cls.__name__} must expose a slots-only instance layout"
        )

    # --- 5. Slots must NOT expose __dict__ or __weakref__
    _assert_no_forbidden_slots(cls)

    # --- 6. Final sanity check (defensive)
    try:
        dummy = object.__new__(cls)
    except Exception:
        # Abstract classes may fail instantiation — that's fine
        return

    if hasattr(dummy, "__dict__"):
        raise StructuralContractViolation(
            f"{cls.__name__} instances expose __dict__ despite slots. "
            "This is forbidden."
        )
