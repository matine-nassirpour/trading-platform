from dataclasses import is_dataclass
from typing import Any


def is_dataclass_instance(value: Any) -> bool:
    """
    Returns True only for dataclass instances.

    IMPORTANT:
    dataclasses.is_dataclass(x) returns True for both:
    - dataclass classes
    - dataclass instances

    Domain-state validation must only traverse instances.
    Dataclass classes are not valid canonical state values.
    """
    return is_dataclass(value) and not isinstance(value, type)
