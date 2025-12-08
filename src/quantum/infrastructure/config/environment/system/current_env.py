from __future__ import annotations

from types import MappingProxyType
from typing import Final

from quantum.infrastructure.config.environment.system.snapshot import get_frozen_env

_ENV_CACHE: Final = MappingProxyType(dict(get_frozen_env()))


def get_current_env() -> str:
    """
    Return the normalized application environment indicator.

    Contract:
        • 'quantum_env' must come from OS, not files
        • empty or missing -> 'dev'
        • strictly lowercase and stripped
    """
    raw = _ENV_CACHE.get("quantum_env", "").strip().lower()
    return raw or "dev"


def is_production() -> bool:
    """Safety-grade production-mode detection."""
    return get_current_env() == "prod"
