from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel

from quantum.infrastructure.config.environment.policy import is_env_routing_strict
from quantum.infrastructure.config.environment.validation import (
    validate_no_unknown_environment_variables,
)


class EnvironmentModelRouter:
    """
    Route environment variables to their respective Pydantic models.
    With strict routing enabled, unknown variables cause immediate failure.
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
        # Strictness: detect unknown variables BEFORE routing
        if is_env_routing_strict():
            validate_no_unknown_environment_variables(models=models, env=env)

        # Route only allowed keys to each model
        return {
            name: EnvironmentModelRouter.extract(model_cls, env)
            for name, model_cls in models.items()
        }
