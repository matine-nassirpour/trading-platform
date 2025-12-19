from dataclasses import fields, is_dataclass
from enum import Enum
from types import UnionType
from typing import Any, Union, get_args, get_origin

from contracts.core.model import ContractModel
from contracts.generators.shared.naming import snake_to_lower_camel


class TypeScriptParserGenerationError(RuntimeError):
    pass


def _is_optional(tp: Any) -> bool:
    origin = get_origin(tp)
    return (origin is Union or origin is UnionType) and type(None) in get_args(tp)


def _strip_optional(tp: Any) -> Any:
    args = [a for a in get_args(tp) if a is not type(None)]
    if len(args) != 1:
        raise TypeScriptParserGenerationError(f"Invalid Optional type: {tp!r}")
    return args[0]


def _is_dict(tp: Any) -> bool:
    return get_origin(tp) is dict


def _is_dict_of(tp: Any, value_type: Any) -> bool:
    origin = get_origin(tp)
    if origin is not dict:
        return False
    key, value = get_args(tp)
    return key is str and value == value_type


def _dict_value_type(tp: Any) -> Any:
    return get_args(tp)[1]


def _ts_expr_for_dict(snake: str, tp: Any, optional: bool) -> str:
    value_tp = _dict_value_type(tp)

    if value_tp is Any:
        return (
            f"o['{snake}'] === null || o['{snake}'] === undefined "
            f"? null "
            f": expectObject(o['{snake}'], '{snake}')"
            if optional
            else f"expectObject(o['{snake}'], '{snake}')"
        )

    if value_tp is str:
        return (
            f"expectOptionalRecordOfString(o['{snake}'], '{snake}')"
            if optional
            else f"expectRecordOfString(o['{snake}'], '{snake}')"
        )

    if _is_optional(value_tp) and _strip_optional(value_tp) is str:
        return f"expectRecordOfOptionalString(o['{snake}'], '{snake}')"

    raise TypeScriptParserGenerationError(
        f"Unsupported dict value type: {value_tp!r} (field {snake})"
    )


def _ts_expr_for_primitive(snake: str, tp: Any, optional: bool) -> str | None:
    if tp is str:
        return (
            f"expectOptionalString(o['{snake}'], '{snake}')"
            if optional
            else f"expectString(o['{snake}'], '{snake}')"
        )

    if tp is bool:
        return (
            f"expectOptionalBoolean(o['{snake}'], '{snake}')"
            if optional
            else f"expectBoolean(o['{snake}'], '{snake}')"
        )

    if tp in (int, float):
        return (
            f"expectOptionalNumber(o['{snake}'], '{snake}')"
            if optional
            else f"expectNumber(o['{snake}'], '{snake}')"
        )

    return None


def _ts_expr_for_enum(snake: str, tp: Any, optional: bool) -> str | None:
    if not (isinstance(tp, type) and issubclass(tp, Enum)):
        return None

    guard = f"expect{tp.__name__}"
    if optional:
        return (
            f"o['{snake}'] === null || o['{snake}'] === undefined "
            f"? null "
            f": {guard}(o['{snake}'], '{snake}')"
        )
    return f"{guard}(o['{snake}'], '{snake}')"


def _ts_expr_for_list(snake: str, tp: Any) -> str | None:
    if get_origin(tp) is not list:
        return None

    (item_type,) = get_args(tp)

    if _is_optional(item_type):
        raise TypeScriptParserGenerationError(
            f"list[Optional[T]] is not allowed in contracts (field {snake})"
        )

    # list[str]
    if item_type is str:
        return f"expectArrayOfString(o['{snake}'], '{snake}')"

    # list[int] / list[float]
    if item_type in (int, float):
        return f"expectArrayOfNumber(o['{snake}'], '{snake}')"

    # list[bool]
    if item_type is bool:
        return f"expectArrayOfBoolean(o['{snake}'], '{snake}')"

    # list[Enum]
    if isinstance(item_type, type) and issubclass(item_type, Enum):
        return (
            f"expectArrayOfEnum("
            f"o['{snake}'], '{snake}', expect{item_type.__name__}"
            f")"
        )

    # list[ContractModel]
    if isinstance(item_type, type) and issubclass(item_type, ContractModel):
        return f"expectArray(o['{snake}'], '{snake}', (v, ctx) => parse{item_type.__name__}(v))"

    raise TypeScriptParserGenerationError(
        f"Unsupported list item type in contract: list[{item_type!r}] "
        f"(field {snake})"
    )


def _ts_expr_for_contract(snake: str, tp: Any, optional: bool) -> str | None:
    if not (isinstance(tp, type) and issubclass(tp, ContractModel)):
        return None

    if optional:
        return (
            f"o['{snake}'] === null || o['{snake}'] === undefined "
            f"? null "
            f": parse{tp.__name__}(o['{snake}'])"
        )

    return f"parse{tp.__name__}(o['{snake}'])"


def _ts_expr_for_field(snake: str, tp: Any) -> str:
    optional = _is_optional(tp)
    if optional:
        tp = _strip_optional(tp)

    for handler in (
        _ts_expr_for_primitive,
        _ts_expr_for_enum,
        _ts_expr_for_list,
        _ts_expr_for_contract,
    ):
        expr = (
            handler(snake, tp, optional)
            if handler != _ts_expr_for_list
            else handler(snake, tp)
        )
        if expr is not None:
            return expr

    if _is_dict(tp):
        return _ts_expr_for_dict(snake, tp, optional)

    raise TypeScriptParserGenerationError(
        f"Unsupported contract field type: {tp!r} (field {snake})"
    )


def generate_ts_parser(model: type[ContractModel]) -> str:
    if not is_dataclass(model):
        raise TypeScriptParserGenerationError(
            "Parser generation requires a dataclass ContractModel"
        )

    lines: list[str] = []

    fn_name = f"parse{model.__name__}"
    lines.append(f"export function {fn_name}(raw: unknown): {model.__name__} {{")
    lines.append(f"  const o = expectObject(raw, '{model.__name__}');")
    lines.append("")
    lines.append("  return {")

    for f in fields(model):
        snake = f.name
        camel = snake_to_lower_camel(snake)
        expr = _ts_expr_for_field(snake, f.type)
        lines.append(f"    {camel}: {expr},")

    lines.append("  };")
    lines.append("}")

    return "\n".join(lines)
