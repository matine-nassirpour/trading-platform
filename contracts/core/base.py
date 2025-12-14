from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Any


class ContractViolation(RuntimeError):
    """Raised when an object violates its declared contract."""


@dataclass(frozen=True)
class ContractModel:
    """
    Base class for all contract DTOs.

    Guarantees:
    - immutability
    - explicit fields
    - serializability
    """

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            result[f.name] = _serialize(value)
        return result


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return value.to_dict()  # type: ignore
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    return value


def assert_contract(instance: Any, contract_type: type[ContractModel]) -> None:
    """
    Runtime assertion that an instance matches a declared contract.
    Used in tests, not in production hot paths.
    """
    if not isinstance(instance, contract_type):
        raise ContractViolation(
            f"Expected {contract_type.__name__}, got {type(instance).__name__}"
        )
