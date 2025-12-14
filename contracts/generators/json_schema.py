from dataclasses import fields, is_dataclass
from typing import Any

from contracts.core.base import ContractModel


def generate_json_schema(model: type[ContractModel]) -> dict[str, Any]:
    if not is_dataclass(model):
        raise TypeError("Contract must be a dataclass")

    properties: dict[str, Any] = {}
    required: list[str] = []

    for f in fields(model):
        properties[f.name] = _field_schema(f.type)
        required.append(f.name)

    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _field_schema(tp: Any) -> dict[str, Any]:
    if tp in (str,):
        return {"type": "string"}
    if tp in (int,):
        return {"type": "integer"}
    if tp in (bool,):
        return {"type": "boolean"}
    if tp in (float,):
        return {"type": "number"}
    if getattr(tp, "__origin__", None) is dict:
        return {"type": "object"}
    if getattr(tp, "__origin__", None) is list:
        return {"type": "array"}
    return {"type": "object"}
