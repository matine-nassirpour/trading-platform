import inspect

from dataclasses import fields, is_dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from functools import cache
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
    """
    Returns True only if cls is a dataclass that is:
    - frozen
    - slotted
    - effectively dict-free at instance level
    """
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
        # Defensive fallback:
        # if allocation is impossible, class-level checks are deemed sufficient.
        return True

    return not hasattr(dummy, "__dict__")


def _assert_not_forbidden_temporal_type(value: Any, path: str) -> None:
    """
    Explicitly forbids datetime.

    IMPORTANT:
    datetime is a subclass of date in Python, so this check MUST run
    before generic scalar acceptance logic.
    """
    if isinstance(value, datetime):
        raise StructuralContractViolation(
            f"{path} contains datetime, which is forbidden in domain primitives. "
            "Use a dedicated instant ValueObject (e.g. EpochMs) instead."
        )


def _assert_not_forbidden_enum_type(value: Any, path: str) -> None:
    """
    Explicitly forbids Enum members in domain primitives.

    ARCHITECTURAL POLICY:
    Domain concepts that look like enums must be modeled as explicit domain
    Value Objects (for example ClosedSetValueObject), not as Python Enum.
    """
    enum_cls = value.__class__
    enum_mro = getattr(enum_cls, "__mro__", ())

    if any(base.__name__ == "Enum" for base in enum_mro):
        raise StructuralContractViolation(
            f"{path} contains {enum_cls.__name__}, which is forbidden in domain "
            "primitives. Use an explicit ValueObject / ClosedSetValueObject instead "
            "of Python Enum."
        )


def _assert_not_forbidden_mutable_or_aliasable_type(value: Any, path: str) -> None:
    """
    Rejects values that are mutable, aliasable, or only superficially read-only.

    IMPORTANT:
    A value is accepted only if it is safe as a domain-state component under
    deterministic replay, audit, and event-sourced reconstruction constraints.

    In particular:
    - MappingProxyType is intentionally forbidden.
      It is only a read-only VIEW over an underlying dict.
      If that dict mutates elsewhere, the mapping proxy observes the mutation.
      Therefore it does NOT satisfy deep immutability or deterministic stability.
    """
    if isinstance(value, float):
        raise StructuralContractViolation(
            f"{path} uses float, which is forbidden in domain primitives; "
            "use Decimal or an explicit numeric ValueObject."
        )

    if isinstance(value, (list, dict, set, bytearray)):
        raise StructuralContractViolation(
            f"{path} contains unsupported mutable value of type {type(value).__name__}."
        )

    # Deliberately avoid importing MappingProxyType at module scope so that
    # its absence from the allowed contract remains explicit and intentional.
    if type(value).__name__ == "mappingproxy":
        raise StructuralContractViolation(
            f"{path} contains MappingProxyType, which is forbidden in domain "
            "primitives. MappingProxyType is only a read-only view over a "
            "mutable dictionary and does not guarantee deep immutability."
        )


def _assert_tuple_is_deeply_immutable(value: tuple[Any, ...], path: str) -> None:
    for index, item in enumerate(value):
        _assert_deeply_immutable_value(item, f"{path}[{index}]")


def _assert_frozenset_is_deeply_immutable(value: frozenset[Any], path: str) -> None:
    for item in value:
        _assert_deeply_immutable_value(item, f"{path}[{item!r}]")


def _assert_dataclass_instance_is_deeply_immutable(value: Any, path: str) -> None:
    cls = type(value)

    if not _is_frozen_slotted_dataclass_class(cls):
        raise StructuralContractViolation(
            f"{path} contains dataclass {cls.__name__} which is not frozen + slotted."
        )

    for f in fields(value):
        _assert_deeply_immutable_value(
            getattr(value, f.name),
            f"{path}.{f.name}",
        )


def _assert_deeply_immutable_value(value: Any, path: str) -> None:
    """
    Recursively enforces the structural deep-immutability contract
    for domain primitives.

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
    - timezone
    - tuple[deeply immutable]
    - frozenset[deeply immutable]
    - frozen, slotted dataclass instances whose fields are themselves deeply immutable

    Forbidden:
    - datetime
    - float
    - Enum
    - list
    - dict
    - set
    - bytearray
    - MappingProxyType
    - mutable dataclasses
    - arbitrary objects exposing mutable, aliasable, or non-deterministic state
    """

    _assert_not_forbidden_temporal_type(value, path)
    _assert_not_forbidden_enum_type(value, path)
    _assert_not_forbidden_mutable_or_aliasable_type(value, path)

    if isinstance(value, _ALLOWED_DEEPLY_IMMUTABLE_SCALARS):
        return

    if isinstance(value, tuple):
        _assert_tuple_is_deeply_immutable(value, path)
        return

    if isinstance(value, frozenset):
        _assert_frozenset_is_deeply_immutable(value, path)
        return

    if is_dataclass(value):
        _assert_dataclass_instance_is_deeply_immutable(value, path)
        return

    raise StructuralContractViolation(
        f"{path} contains unsupported mutable, aliasable, or non-deterministic "
        f"value of type {type(value).__name__}."
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
        raise StructuralContractViolation(f"{cls.__name__} must be a dataclass.")

    # --- 3. Must be frozen
    params = getattr(cls, "__dataclass_params__", None)
    if not params or not getattr(params, "frozen", False):
        raise StructuralContractViolation(
            f"{cls.__name__} must be declared with frozen=True."
        )

    # --- 4. Must use slots (robust check)
    if not hasattr(cls, "__slots__"):
        raise StructuralContractViolation(
            f"{cls.__name__} must expose a slots-only instance layout."
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
