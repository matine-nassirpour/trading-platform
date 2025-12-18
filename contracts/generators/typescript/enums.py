from enum import Enum


class TypeScriptEnumGenerationError(RuntimeError):
    pass


def generate_ts_enum(enum: type[Enum]) -> str:
    """
    Generate a strict TypeScript string-literal union
    from a contractual Python Enum.
    """

    if not issubclass(enum, Enum):
        raise TypeScriptEnumGenerationError(f"{enum!r} is not a Python Enum")

    values = [repr(member.value) for member in enum]

    if not values:
        raise TypeScriptEnumGenerationError(f"Enum {enum.__name__} has no values")

    return f"export type {enum.__name__} = " + " | ".join(values) + ";"
