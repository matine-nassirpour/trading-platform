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


def assert_canonical_domain_state_value(value: Any, path: str) -> None:
    """
    Recursively validates a value against the canonical domain-state policy.

    This policy is STRICTER than pure deep immutability.

    It enforces:
    - deep immutability
    - replay-safe modeling constraints
    - explicit domain-state representation discipline

    Additional canonical-domain rules currently include:
    - datetime is forbidden
    - Enum is forbidden
    """
    _assert_not_forbidden_temporal_type(value, path)
    _assert_not_forbidden_enum_type(value, path)

    assert_deeply_immutable_value(value, path)

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
