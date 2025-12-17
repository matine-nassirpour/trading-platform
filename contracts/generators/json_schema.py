from dataclasses import fields, is_dataclass
from typing import Any

from contracts.core.base import ContractModel
from contracts.generators.naming import snake_to_lower_camel


def generate_json_schema(model: type[ContractModel]) -> dict[str, Any]:
    if not is_dataclass(model):
        raise TypeError("Contract must be a dataclass")

    properties: dict[str, Any] = {}
    required: list[str] = []

    for f in fields(model):
        field_name = snake_to_lower_camel(f.name)
        properties[field_name] = _field_schema(f.type)
        required.append(field_name)

    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _field_schema(tp: Any) -> dict[str, Any]:
    if tp is str:
        return {"type": "string"}
    if tp is int:
        return {"type": "integer"}
    if tp is bool:
        return {"type": "boolean"}
    if tp is float:
        return {"type": "number"}
    if getattr(tp, "__origin__", None) is dict:
        return {"type": "object"}
    if getattr(tp, "__origin__", None) is list:
        return {"type": "array"}
    return {"type": "object"}
