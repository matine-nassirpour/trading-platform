from __future__ import annotations

from collections.abc import Mapping


class UnknownEnvironmentVariablesError(ValueError):
    """Raised when unknown environment variables are detected in strict mode."""


def validate_no_unknown_environment_variables(
    *,
    models: Mapping[str, type],
    env: Mapping[str, str],
) -> None:
    """
    Fail-fast validation ensuring NO unknown variables exist in the environment.

    Safety-critical guarantees:
        • Pure function (no side effects)
        • Deterministic ordering
        • Exhaustive listing of unknown variables
        • Aligns environment input strictly with model declarations
    """
    allowed: set[str] = set()
    for model_cls in models.values():
        allowed.update(model_cls.model_fields.keys())

    # Unknown = variables not belonging to ANY model
    unknown = sorted(set(env.keys()) - allowed)

    if not unknown:
        return

    # Build deterministic error message
    lines: list[str] = []
    lines.append("Unknown environment variables detected.")
    lines.append("These keys do not correspond to any declared configuration model:")
    lines.append("")
    for key in unknown:
        lines.append(f"  - {key!r}")
    lines.append("")
    lines.append("Strict environment routing is enabled. Aborting.")

    raise UnknownEnvironmentVariablesError("\n".join(lines))
