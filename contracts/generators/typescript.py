from dataclasses import fields, is_dataclass

from contracts.core.base import ContractModel


def generate_ts_interface(model: type[ContractModel]) -> str:
    if not is_dataclass(model):
        raise TypeError("Contract must be a dataclass")

    lines = [f"export interface {model.__name__} {{"]

    for f in fields(model):
        ts_type = _map_type(f.type)
        lines.append(f"  {f.name}: {ts_type};")

    lines.append("}")
    return "\n".join(lines)


def _map_type(tp) -> str:
    if tp is str:
        return "string"
    if tp is int or tp is float:
        return "number"
    if tp is bool:
        return "boolean"
    if getattr(tp, "__origin__", None) is list:
        return "any[]"
    if getattr(tp, "__origin__", None) is dict:
        return "{ [key: string]: any }"
    return "any"
