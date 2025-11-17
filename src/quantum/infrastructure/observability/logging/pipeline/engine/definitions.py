from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class StepFactory(Protocol):
    def __call__(self, bundle: Any | None = None) -> Any: ...


@dataclass(frozen=True)
class StepDefinition:
    """
    Declarative, immutable definition of a pipeline step.
    - key: logical identifier (stable, versioned)
    - enabled_flag: name of the boolean config field enabling this step
    - factory: constructor or factory function returning a step instance
    """

    key: str
    enabled_flag: str
    factory: StepFactory
