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
