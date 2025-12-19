from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
from typing import Any

from contracts.core.validation import validate_contract
from contracts.core.wire_format import assert_snake_case


def _serialize(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, ContractModel):
        return value.to_dict()

    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]

    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}

    return value


@dataclass(frozen=True)
class ContractModel:
    """
    Base class for all contract DTOs.

    Guarantees:
    - immutability
    - explicit fields
    - deterministic serialization
    - strict snake_case wire format
    - runtime contract validation
    """

    def __post_init__(self) -> None:
        validate_contract(self)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for f in fields(self):
            assert_snake_case(f.name)
            value = getattr(self, f.name)
            result[f.name] = _serialize(value)
        return result
