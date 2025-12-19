from dataclasses import fields, is_dataclass
from enum import Enum
from types import UnionType
from typing import Any, Union, get_args, get_origin

from contracts.core.model import ContractModel


def _strip_optional(tp: Any) -> Any:
    args = [a for a in get_args(tp) if a is not type(None)]
    if len(args) != 1:
        raise TypeError(f"Invalid Optional type: {tp!r}")
    return args[0]


def _is_optional(tp: Any) -> bool:
    origin = get_origin(tp)
    return (origin is Union or origin is UnionType) and type(None) in get_args(tp)


def _schema_for_optional(tp: Any, defs: dict[str, Any]) -> dict[str, Any] | None:
    if not _is_optional(tp):
        return None

    inner = _strip_optional(tp)
    return {
        "anyOf": [
            _schema_for_type(inner, defs),
            {"type": "null"},
        ]
    }


def _schema_for_any(tp: Any) -> dict[str, Any] | None:
    if tp is Any:
        return {}
    return None


def _schema_for_primitive(tp: Any) -> dict[str, Any] | None:
    if tp is str:
        return {"type": "string"}
    if tp is int:
        return {"type": "integer"}
    if tp is bool:
        return {"type": "boolean"}
    if tp is float:
        return {"type": "number"}
    return None


def _schema_for_enum(tp: Any) -> dict[str, Any] | None:
    if not (isinstance(tp, type) and issubclass(tp, Enum)):
        return None

    values = [member.value for member in tp]

    if not values:
        raise TypeError(f"Enum {tp.__name__} has no values")

    # Enforce string-based enums only
    if not all(isinstance(v, str) for v in values):
        raise TypeError(
            f"Invalid contract enum {tp.__name__}: " f"all enum values must be strings"
        )

    return {
        "type": "string",
        "enum": values,
    }


def _schema_for_list(tp: Any, defs: dict[str, Any]) -> dict[str, Any] | None:
    if get_origin(tp) is list:
        (item,) = get_args(tp)
        return {
            "type": "array",
            "items": _schema_for_type(item, defs),
        }
    return None


def _schema_for_dict(tp: Any, defs: dict[str, Any]) -> dict[str, Any] | None:
    if get_origin(tp) is dict:
        key, value = get_args(tp)
        if key is not str:
            raise TypeError("Only dict[str, T] is allowed in contracts")
        return {
            "type": "object",
            "additionalProperties": _schema_for_type(value, defs),
        }
    return None


def _schema_for_contract(
    tp: Any,
    defs: dict[str, Any],
) -> dict[str, Any] | None:
    if not (isinstance(tp, type) and issubclass(tp, ContractModel)):
        return None

    name = tp.__name__
    if name in defs:
        return {"$ref": f"#/$defs/{name}"}

    properties: dict[str, Any] = {}
    required: list[str] = []

    for f in fields(tp):
        properties[f.name] = _schema_for_type(f.type, defs)
        if not _is_optional(f.type):
            required.append(f.name)

    defs[name] = {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }

    return {"$ref": f"#/$defs/{name}"}


def _schema_for_type(tp: Any, defs: dict[str, Any]) -> dict[str, Any]:
    for handler in (
        _schema_for_optional,
        _schema_for_any,
        _schema_for_primitive,
        _schema_for_enum,
        _schema_for_list,
        _schema_for_dict,
        _schema_for_contract,
    ):
        schema = (
            handler(tp, defs)
            if handler
            in (
                _schema_for_optional,
                _schema_for_list,
                _schema_for_dict,
                _schema_for_contract,
            )
            else handler(tp)
        )
        if schema is not None:
            return schema

    raise TypeError(f"Unsupported contract type: {tp!r}")


def generate_json_schema(model: type[ContractModel]) -> dict[str, Any]:
    if not is_dataclass(model):
        raise TypeError("Contract must be a dataclass")

    defs: dict[str, Any] = {}
    root = _schema_for_contract(model, defs)

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **root,
        "$defs": defs,
    }
