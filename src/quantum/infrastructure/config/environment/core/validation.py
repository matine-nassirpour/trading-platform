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
    reserved: set[str] | None = None,
) -> None:
    """
    Fail-fast environmental validation.

    • reserved: keys allowed even if not declared in models
    """
    reserved = reserved or set()

    allowed = set()
    for model_cls in models.values():
        allowed.update(model_cls.model_fields.keys())

    allowed |= reserved

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
