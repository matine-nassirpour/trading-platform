from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from types import UnionType
from typing import Any, Union, get_args, get_origin


class ContractViolation(RuntimeError):
    """Raised when an object violates its declared contract."""


def _is_optional(tp: Any) -> bool:
    origin = get_origin(tp)
    return (origin is Union or origin is UnionType) and type(None) in get_args(tp)


def _strip_optional(tp: Any) -> Any:
    args = [a for a in get_args(tp) if a is not type(None)]
    if len(args) != 1:
        raise ContractViolation(f"Invalid Optional type: {tp!r}")
    return args[0]


def _validate_model(instance: Any, path: str) -> None:
    cls = instance.__class__

    if not is_dataclass(cls):
        raise ContractViolation(f"{path}: ContractModel must be a dataclass")

    for field in fields(cls):
        value = getattr(instance, field.name)
        field_path = f"{path}.{field.name}"
        _validate_value(value, field.type, field_path)


def _validate_optional(value: Any, expected_type: Any, path: str) -> None:
    inner = _strip_optional(expected_type)
    if value is None:
        return
    _validate_value(value, inner, path)


def _validate_primitive(value: Any, expected_type: Any, path: str) -> bool:
    if expected_type not in (str, int, bool, float):
        return False

    if not isinstance(value, expected_type):
        raise ContractViolation(
            f"{path}: expected {expected_type.__name__}, got {type(value).__name__}"
        )
    return True


def _validate_enum(value: Any, expected_type: Any, path: str) -> bool:
    if not (isinstance(expected_type, type) and issubclass(expected_type, Enum)):
        return False

    if not isinstance(value, expected_type):
        raise ContractViolation(
            f"{path}: expected enum {expected_type.__name__}, got {value!r}"
        )
    return True


def _safe_isinstance(value: Any, tp: Any) -> bool:
    if not isinstance(tp, type):
        return False
    if getattr(tp, "_is_protocol", False):
        raise ContractViolation(
            f"Protocol {tp.__name__} cannot be used for runtime validation"
        )
    return isinstance(value, tp)


def _validate_dataclass(value: Any, expected_type: Any, path: str) -> bool:
    if not (isinstance(expected_type, type) and is_dataclass(expected_type)):
        return False

    if not _safe_isinstance(value, expected_type):
        raise ContractViolation(
            f"{path}: expected {expected_type.__name__}, got {type(value).__name__}"
        )

    _validate_model(value, path)
    return True


def _validate_list(value: Any, expected_type: Any, path: str) -> bool:
    if get_origin(expected_type) is not list:
        return False

    if not isinstance(value, list):
        raise ContractViolation(f"{path}: expected list")

    (item_type,) = get_args(expected_type)
    for idx, item in enumerate(value):
        _validate_value(item, item_type, f"{path}[{idx}]")

    return True


def _validate_dict(value: Any, expected_type: Any, path: str) -> bool:
    if get_origin(expected_type) is not dict:
        return False

    key_type, value_type = get_args(expected_type)

    if key_type is not str:
        raise ContractViolation(f"{path}: only dict[str, T] is allowed in contracts")

    if not isinstance(value, dict):
        raise ContractViolation(f"{path}: expected dict")

    for k, v in value.items():
        if not isinstance(k, str):
            raise ContractViolation(f"{path}: invalid dict key {k!r} (must be str)")
        _validate_value(v, value_type, f"{path}.{k}")

    return True


def _validate_value(value: Any, expected_type: Any, path: str) -> None:
    if _is_optional(expected_type):
        _validate_optional(value, expected_type, path)
        return

    if value is None:
        raise ContractViolation(f"{path}: null value is not allowed")

    validators = (
        _validate_primitive,
        _validate_enum,
        _validate_dataclass,
        _validate_list,
        _validate_dict,
    )

    for validator in validators:
        if validator(value, expected_type, path):
            return

    if expected_type is Any:
        return

    raise ContractViolation(f"{path}: unsupported contract type {expected_type!r}")


def validate_contract(instance: Any) -> None:
    """
    Validate a contract instance against its declared annotations.
    """
    _validate_model(instance, path=instance.__class__.__name__)
