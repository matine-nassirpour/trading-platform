from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from quantum.infrastructure.observability.logging.pipeline.engine.argument_kind import (
    StepArgumentKind,
)


class StepFactory(Protocol):
    def __call__(self, bundle: Any | None = None) -> Any: ...


@dataclass(frozen=True)
class StepDefinition:
    """
    Declarative, immutable definition of a pipeline step.
    - key: stable identifier
    - enabled_flag: bool field in PipelineConfig
    - factory: function/builder returning a PipelineStep instance
    - arg_kind: declares exactly what argument factory expects
    """

    key: str
    enabled_flag: str
    factory: StepFactory
    arg_kind: StepArgumentKind
