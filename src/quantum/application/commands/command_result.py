from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class CommandResult(Generic[T]):
    """
    Standardized result wrapper for commands.
    """

    value: T | None = None
    success: bool = True
    message: str | None = None
