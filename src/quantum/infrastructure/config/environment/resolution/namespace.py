from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel

from quantum.infrastructure.config.environment.core.prefixes import (
    derive_prefixes_from_models,
)


def extract_application_env(
    env: Mapping[str, str], *, models: Mapping[str, type[BaseModel]]
) -> dict[str, str]:
    """
    Extract only environment variables relevant to the application namespace.

    Strategy:
        • Keep only keys starting with known prefixes (e.g., 'quantum_')
        • Ignore all OS/system/editor variables
        • Pure, deterministic, safety-grade

    Guarantees:
        • Strict routing applies only to application config keys
        • System variables are ignored completely
    """

    prefixes = derive_prefixes_from_models(models=models)

    return {
        k: v for k, v in env.items() if any(k.startswith(prefix) for prefix in prefixes)
    }
