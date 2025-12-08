from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel


class UnknownEnvironmentVariablesError(ValueError):
    """Raised when unknown environment variables are detected in strict mode."""


def validate_no_unknown_environment_variables(
    *,
    models: Mapping[str, type[BaseModel]],
    env: Mapping[str, Any],
) -> None:
    """
    Fail-fast validation ensuring NO unknown variables exist in the environment.

    Safety-critical guarantees:
        • Pure function (no side effects)
        • Deterministic ordering
        • Exhaustive listing of unknown variables
        • Aligns environment input strictly with model declarations
    """
    allowed = set()
    for model_cls in models.values():
        allowed.update(model_cls.model_fields.keys())

    # Unknown = variables not belonging to ANY model
    unknown = sorted(set(env.keys()) - allowed)

    if not unknown:
        return

    msg = "\n".join(
        [
            "Unknown environment variables detected.",
            "These keys do not correspond to any declared configuration model:",
            "",
        ]
        + [f"  - {key!r}" for key in unknown]
        + ["", "Strict environment routing is enabled. Aborting."]
    )

    raise UnknownEnvironmentVariablesError(msg)
