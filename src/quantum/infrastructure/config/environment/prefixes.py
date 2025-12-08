from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel


def derive_prefixes_from_models(
    models: Mapping[str, type[BaseModel]],
) -> tuple[str, ...]:
    """
    Compute allowed prefixes dynamically from model field names.

    Example:
        CoreSettings → quantum_app_name → prefix 'quantum_'
    """
    prefixes: set[str] = set()

    for model_cls in models.values():
        for field in model_cls.model_fields.keys():
            if "_" in field:
                idx = field.find("_") + 1
                base = field[:idx]
                prefixes.add(base)

    # Deterministic ordering
    return tuple(sorted(prefixes))
