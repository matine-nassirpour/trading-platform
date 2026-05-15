from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from quantum.domain.shared_kernel.foundation.contracts.deep_immutability import (
    assert_deeply_immutable_value,
)
from quantum.domain.shared_kernel.foundation.contracts.violations import (
    StructuralContractViolation,
)


def _assert_not_forbidden_temporal_type(value: Any, path: str) -> None:
    """
    Canonical domain-state modeling rule.

    Python datetime is forbidden inside canonical domain state.

    RATIONALE:
    - timezone ambiguity
    - serialization ambiguity
    - replay drift risk
    - desire for explicit domain temporal Value Objects
    """
    if isinstance(value, datetime):
        raise StructuralContractViolation(
            f"{path} contains datetime, which is forbidden in canonical domain "
            "state. Use an explicit domain temporal ValueObject instead."
        )


def _assert_not_forbidden_enum_type(value: Any, path: str) -> None:
    """
    Canonical domain-state modeling rule.

    Python Enum is forbidden inside canonical domain state.

    RATIONALE:
    - implicit serialization conventions
    - fragile cross-boundary representation semantics
    - preference for explicit Value Objects / closed-set domain types
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

    RATIONALE:
    - frozenset is immutable but unordered
    - unordered state is not suitable for canonical serialization
    - event-sourced replay must be deterministic
    - snapshots, hashes, signatures and projections require stable ordering

    Use tuple[...] with explicit deterministic business ordering instead.
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
    - datetime is forbidden
    - Enum is forbidden
    - frozenset is forbidden

    IMPORTANT:
    frozenset remains potentially acceptable for non-canonical internal
    structures validated only by deep immutability, but it is forbidden in
    canonical replayable domain state.
    """
    _assert_canonical_domain_state_value_shallow(value, path)

    assert_deeply_immutable_value(value, path)

    if isinstance(value, tuple):
        for index, item in enumerate(value):
            assert_canonical_domain_state_value(item, f"{path}[{index}]")
        return

    if is_dataclass(value):
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
    if not is_dataclass(instance):
        raise StructuralContractViolation(
            f"{type(instance).__name__} must be a dataclass instance."
        )

    for f in fields(instance):
        assert_canonical_domain_state_value(
            getattr(instance, f.name),
            f"{type(instance).__name__}.{f.name}",
        )
