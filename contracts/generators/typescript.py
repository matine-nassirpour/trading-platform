from dataclasses import fields, is_dataclass
from types import UnionType
from typing import Any, Union, get_args, get_origin

from contracts.core.base import ContractModel


class TypeScriptGenerationError(RuntimeError):
    """Raised when a contract cannot be mapped to TypeScript safely."""


def _is_optional(tp: Any) -> bool:
    """
    Return True if tp is Optional[T] or T | None.
    """
    origin = get_origin(tp)

    if origin is Union:
        return type(None) in get_args(tp)

    if origin is UnionType:
        return type(None) in get_args(tp)

    return False


def _strip_optional(tp: Any) -> Any:
    """
    Given Optional[T] or T | None, return T.
    """
    args = tuple(arg for arg in get_args(tp) if arg is not type(None))
    if len(args) != 1:
        raise TypeScriptGenerationError(
            f"Optional type must wrap exactly one concrete type, got {tp!r}"
        )
    return args[0]


def _map_primitive(tp: Any) -> str | None:
    if tp is str:
        return "string"
    if tp in (int, float):
        return "number"
    if tp is bool:
        return "boolean"
    return None


def _map_collection(tp: Any) -> str | None:
    origin = get_origin(tp)
    args = get_args(tp)

    if origin is list:
        if not args:
            raise TypeScriptGenerationError("List without item type is forbidden")
        return f"ReadonlyArray<{_map_type(args[0])}>"

    if origin is dict:
        key, value = args
        if key is not str:
            raise TypeScriptGenerationError("Only dict[str, T] is allowed in contracts")
        if value is Any:
            return "Readonly<Record<string, unknown>>"
        return f"Readonly<Record<string, {_map_type(value)}>>"

    return None


def _map_type(tp: Any) -> str:
    """
    Map a Python type annotation to a strict TypeScript type.
    """

    if _is_optional(tp):
        return f"{_map_type(_strip_optional(tp))} | null"

    primitive = _map_primitive(tp)
    if primitive is not None:
        return primitive

    collection = _map_collection(tp)
    if collection is not None:
        return collection

    # Nested ContractModel
    if isinstance(tp, type) and issubclass(tp, ContractModel):
        return tp.__name__

    # Fallback — forbidden implicit openness
    raise TypeScriptGenerationError(
        f"Unsupported contract type for TypeScript generation: {tp!r}"
    )


def generate_ts_interface(model: type[ContractModel]) -> str:
    """
    Generate a strict, readonly TypeScript interface from a ContractModel.

    Guarantees:
    - No `any`
    - Deterministic output
    - Angular-compatible
    - Immutable by default
    """
    if not is_dataclass(model):
        raise TypeError("Contract must be a dataclass")

    lines: list[str] = [f"export interface {model.__name__} {{"]

    for f in fields(model):
        ts_type = _map_type(f.type)
        lines.append(f"  readonly {f.name}: {ts_type};")

    lines.append("}")
    return "\n".join(lines)
