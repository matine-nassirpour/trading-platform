from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel


class EnvironmentModelRouter:
    """
    Responsibilities:
        • Extract exactly the environment variables belonging to each Pydantic model.
        • Automatically adapts to model evolution (field additions/removals).
        • Ignores unknown variables safely (never passed to models).
        • Pure, deterministic, zero side effects, fully testable.
        • Clean Architecture compliant (routing concerns isolated from models).
        • Safety-critical design: contract of valid inputs = declared model fields.
    """

    @staticmethod
    def extract(model_cls: type[BaseModel], env: Mapping[str, Any]) -> dict[str, Any]:
        """
        Produce a dictionary containing ONLY fields declared by model_cls.
        Unknown env vars are ignored safely, never passed to the model.
        """
        allowed = model_cls.model_fields.keys()
        return {k: env[k] for k in allowed if k in env}

    @staticmethod
    def route(
        models: Mapping[str, type[BaseModel]],
        env: Mapping[str, Any],
    ) -> dict[str, dict[str, Any]]:
        """
        This allows future models to be added with zero code changes.
        Returns:
             dict: model_name → extracted_subset_of_env.
        """
        return {
            name: EnvironmentModelRouter.extract(model_cls, env)
            for name, model_cls in models.items()
        }


def find_orphan_environment_variables(
    models: Mapping[str, type[BaseModel]],
    env: Mapping[str, Any],
) -> set[str]:
    """
    Return the set of environment variables that do not belong to ANY model.

    Industry-grade optional tool:
        • Useful for diagnostics
        • Allows warnings when strictness required
        • Pure and deterministic
    """
    allowed = set()
    for model_cls in models.values():
        allowed.update(model_cls.model_fields.keys())
    return set(env.keys()) - allowed


def validate_environment_keys_strict(
    models: Mapping[str, type[BaseModel]],
    env: Mapping[str, str],
) -> None:
    """
    Strict structural validation of environment variables.

    Enforces:
        • exact lowercase match to Pydantic field names
        • rejects uppercase or mixed-case aliases
        • ignores unknown OS-level variables
        • safety-critical fail-fast behavior

    Only case-violations produce an error.
    Unknown environment variables are intentionally ignored.
    """

    allowed_fields = set().union(*(m.model_fields.keys() for m in models.values()))

    invalid_case = []

    for key in env.keys():
        if key not in allowed_fields and key.lower() in allowed_fields:
            invalid_case.append((key, key.lower()))

    # If there are no case violations → OK
    if not invalid_case:
        return

    lines = []
    lines.append("Invalid environment configuration detected.")
    lines.append("")
    lines.append("Case violations detected (uppercase or mixed-case variables):")
    for key, expected in invalid_case:
        lines.append(f"   - {key!r} → invalid case (expected {expected!r})")
    lines.append("")
    lines.append("Strict naming rules:")
    lines.append("  • lowercase snake_case only")
    lines.append("  • no uppercase or mixed-case variants")
    lines.append("  • must match Pydantic model fields exactly")
    lines.append("")
    lines.append("Load aborted to prevent ambiguous or unsafe configuration.")

    raise ValueError("\n".join(lines))
