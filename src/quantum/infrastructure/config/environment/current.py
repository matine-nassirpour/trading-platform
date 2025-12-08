from __future__ import annotations

from typing import Final

from quantum.infrastructure.config.environment.normalization import normalize_env_keys
from quantum.infrastructure.config.environment.snapshot import get_frozen_env

_ENV_CACHE: Final[dict[str, str]] = normalize_env_keys(get_frozen_env())


def get_current_env() -> str:
    """
    Normalized source of truth for environment indicators.
    Never reads os.environ directly, always NFKC-normalized lowercase.
    """
    return _ENV_CACHE.get("quantum_env", "dev").strip().lower()


def is_production() -> bool:
    """Safety-grade production-mode detection."""
    return get_current_env() == "prod"
