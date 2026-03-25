from collections.abc import Hashable
from dataclasses import fields, is_dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from functools import cache
from types import MappingProxyType
from typing import Any, cast
from uuid import UUID

from quantum.domain.shared_kernel.foundation.contracts.violations import (
    StructuralContractViolation,
)

_ALLOWED_SCALAR_TYPES = (
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


def _assert_not_forbidden_temporal_type(value: Any, path: str) -> None:
    """
    Business-level modeling rule:
    datetime is forbidden inside deeply immutable domain state.

    Rationale:
    - timezone ambiguity
    - serialization ambiguity
    - replay drift risk
    - desire for explicit domain time value objects
    """
    if isinstance(value, datetime):
        raise StructuralContractViolation(
            f"{path} contains datetime, which is forbidden in deeply immutable "
            "domain state. Use an explicit domain temporal ValueObject instead."
        )


def _assert_not_forbidden_enum_type(value: Any, path: str) -> None:
    """
    Business-level modeling rule:
    Python Enum is forbidden in deeply immutable domain state.
    """
    if isinstance(value, Enum):
        raise StructuralContractViolation(
            f"{path} contains {type(value).__name__}, which is forbidden in deeply "
            "immutable domain state. Use an explicit ValueObject instead."
        )


def _assert_not_forbidden_mutable_or_aliasable_type(value: Any, path: str) -> None:
    """
    Deep immutability / replay-safety policy.

    Forbids mutable or aliasable runtime structures.
    """
    if isinstance(value, float):
        raise StructuralContractViolation(
            f"{path} uses float, which is forbidden. "
            "Use Decimal or an explicit numeric ValueObject."
        )

    if isinstance(value, (list, dict, set, bytearray)):
        raise StructuralContractViolation(
            f"{path} contains mutable value of type {type(value).__name__}, "
            "which is forbidden."
        )

    if isinstance(value, MappingProxyType):
        raise StructuralContractViolation(
            f"{path} contains MappingProxyType, which is forbidden because it is "
            "only a read-only view over an underlying mutable mapping."
        )


def _try_validate_tuple(value: Any, path: str) -> bool:
    if not isinstance(value, tuple):
        return False

    for index, item in enumerate(value):
        assert_deeply_immutable_value(item, f"{path}[{index}]")

    return True


def _try_validate_frozenset(value: Any, path: str) -> bool:
    if not isinstance(value, frozenset):
        return False

    for item in value:
        assert_deeply_immutable_value(item, f"{path}[{item!r}]")

    return True


def _try_validate_dataclass(value: Any, path: str) -> bool:
    if not is_dataclass(value):
        return False

    cls: type[Any] = type(value)

    if not _is_frozen_slotted_dataclass_class(cast(Hashable, cls)):
        raise StructuralContractViolation(
            f"{path} contains dataclass {cls.__name__} which is not "
            "frozen + slotted + dict-free."
        )

    for f in fields(value):
        assert_deeply_immutable_value(
            getattr(value, f.name),
            f"{path}.{f.name}",
        )

    return True


@cache
def _is_frozen_slotted_dataclass_class(cls: Hashable) -> bool:
    """
    Returns True if cls is a frozen, slotted dataclass with no instance __dict__.

    This helper exists because nested dataclass instances may appear inside
    deeply immutable field graphs.
    """
    if not isinstance(cls, type):
        return False

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
        return True

    return not hasattr(dummy, "__dict__")


def assert_deeply_immutable_value(value: Any, path: str) -> None:
    """
    Recursively validates a value against the canonical deep-immutability policy.

    Allowed:
    - immutable scalar types
    - tuple[deeply immutable]
    - frozenset[deeply immutable]
    - frozen, slotted dataclass instances whose fields are deeply immutable

    Forbidden:
    - datetime
    - Enum
    - float
    - list / dict / set / bytearray
    - MappingProxyType
    - mutable / non-slotted dataclass instances
    - arbitrary objects
    """
    _assert_not_forbidden_temporal_type(value, path)
    _assert_not_forbidden_enum_type(value, path)
    _assert_not_forbidden_mutable_or_aliasable_type(value, path)

    if isinstance(value, _ALLOWED_SCALAR_TYPES):
        return

    if _try_validate_tuple(value, path):
        return

    if _try_validate_frozenset(value, path):
        return

    if _try_validate_dataclass(value, path):
        return

    raise StructuralContractViolation(
        f"{path} contains unsupported value of type {type(value).__name__}. "
        "Only explicitly allowed deeply immutable structures may appear in "
        "deep domain state."
    )


def validate_deep_immutability_of_dataclass_instance(instance: object) -> None:
    """
    Validates every dataclass field of an instance against the deep-immutability
    policy.
    """
    if not is_dataclass(instance):
        raise StructuralContractViolation(
            f"{type(instance).__name__} must be a dataclass instance."
        )

    for f in fields(instance):
        assert_deeply_immutable_value(
            getattr(instance, f.name),
            f"{type(instance).__name__}.{f.name}",
        )
