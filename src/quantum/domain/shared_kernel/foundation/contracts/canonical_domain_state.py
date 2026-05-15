from dataclasses import fields
from datetime import date, datetime, time, timedelta, timezone
from enum import Enum
from typing import Any

from quantum.domain.shared_kernel.foundation.contracts.dataclass_introspection import (
    is_dataclass_instance,
)
from quantum.domain.shared_kernel.foundation.contracts.deep_immutability import (
    assert_deeply_immutable_value,
)
from quantum.domain.shared_kernel.foundation.contracts.violations import (
    StructuralContractViolation,
)

_FORBIDDEN_CANONICAL_TEMPORAL_TYPES = (
    datetime,
    date,
    time,
    timedelta,
    timezone,
)


def _assert_not_forbidden_temporal_type(value: Any, path: str) -> None:
    """
    Canonical domain-state modeling rule.

    Native Python temporal types are forbidden inside canonical domain state.

    RATIONALE:
    - timezone ambiguity
    - serialization ambiguity
    - precision ambiguity
    - replay drift risk
    - source-clock ambiguity
    - market-calendar ambiguity
    - desire for explicit domain temporal Value Objects
    """
    if isinstance(value, _FORBIDDEN_CANONICAL_TEMPORAL_TYPES):
        raise StructuralContractViolation(
            f"{path} contains native temporal type {type(value).__name__}, "
            "which is forbidden in canonical domain state. Use an explicit "
            "domain temporal ValueObject instead."
        )


def _assert_not_forbidden_enum_type(value: Any, path: str) -> None:
    """
    Canonical domain-state modeling rule.

    Python Enum is forbidden inside canonical domain state.
    """
    if isinstance(value, Enum):
        raise StructuralContractViolation(
            f"{path} contains {type(value).__name__}, which is forbidden in "
            "canonical domain state. Use an explicit ValueObject instead."
        )


def _assert_not_forbidden_unordered_collection(value: Any, path: str) -> None:
    """
    Canonical domain-state modeling rule.

    frozenset is forbidden inside canonical domain state.
    """
    if isinstance(value, frozenset):
        raise StructuralContractViolation(
            f"{path} contains frozenset, which is forbidden in canonical domain "
            "state because it is unordered. Use tuple[...] with explicit "
            "deterministic ordering instead."
        )


def _assert_canonical_domain_state_value_shallow(value: Any, path: str) -> None:
    """
    Applies all shallow canonical-domain-state prohibitions before recursive
    traversal.
    """
    _assert_not_forbidden_temporal_type(value, path)
    _assert_not_forbidden_enum_type(value, path)
    _assert_not_forbidden_unordered_collection(value, path)


def assert_canonical_domain_state_value(value: Any, path: str) -> None:
    """
    Recursively validates a value against the canonical domain-state policy.

    This policy is STRICTER than pure deep immutability.

    It enforces:
    - deep immutability
    - replay-safe modeling constraints
    - explicit domain-state representation discipline
    - deterministic ordered canonical collections

    Additional canonical-domain rules currently include:
    - native Python temporal types are forbidden
    - Enum is forbidden
    - frozenset is forbidden
    """
    _assert_canonical_domain_state_value_shallow(value, path)

    assert_deeply_immutable_value(value, path)

    if isinstance(value, tuple):
        for index, item in enumerate(value):
            assert_canonical_domain_state_value(item, f"{path}[{index}]")
        return

    if is_dataclass_instance(value):
        for f in fields(value):
            assert_canonical_domain_state_value(
                getattr(value, f.name),
                f"{path}.{f.name}",
            )
        return


def validate_canonical_domain_state_of_dataclass_instance(instance: object) -> None:
    """
    Validates every dataclass field of an instance against the canonical
    domain-state policy.
    """
    if not is_dataclass_instance(instance):
        raise StructuralContractViolation(
            f"{type(instance).__name__} must be a dataclass instance."
        )

    for f in fields(instance):
        assert_canonical_domain_state_value(
            getattr(instance, f.name),
            f"{type(instance).__name__}.{f.name}",
        )
