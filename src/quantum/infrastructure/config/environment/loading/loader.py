from __future__ import annotations

from pathlib import Path

from dotenv import dotenv_values

from quantum.infrastructure.config.environment.core.normalization import (
    normalize_env_keys,
)
from quantum.infrastructure.config.environment.core.types import EnvResolutionResult
from quantum.infrastructure.config.environment.policy.constants import RESERVED_ENV_KEYS
from quantum.infrastructure.config.environment.resolution.namespace import (
    extract_application_env,
)
from quantum.infrastructure.config.environment.system.current_env import (
    get_current_env,
    is_production,
)
from quantum.infrastructure.config.environment.system.snapshot import get_frozen_env
from quantum.infrastructure.config.runtime.registry import CONFIG_MODELS
from quantum.infrastructure.config.runtime.state.config_state import ConfigStateManager


def _load_env_files(base_dir: Path, env_file: Path | None) -> dict[str, str]:
    """
    File-only loader.
    Uses current_env only to select layered files.
    Never merges OS env here.
    """

    current_env = get_current_env()
    prod_mode = is_production()

    # Explicit file
    if env_file:
        return dotenv_values(env_file) or {}

    # Production strict
    if prod_mode:
        return dotenv_values(base_dir / ".env") or {}

    # Non-production layered
    env_base = dotenv_values(base_dir / ".env") or {}
    env_specific = dotenv_values(base_dir / f".env.{current_env}") or {}
    env_local = dotenv_values(base_dir / ".env.local") or {}

    merged = {}
    for layer in (env_base, env_specific, env_local):
        for k, v in layer.items():
            if v is not None:
                merged[k] = v
    return merged


def load_env_from_resolved(
    resolution: EnvResolutionResult,
    *,
    root_param: str | Path | None,
    env_file_param: str | Path | None,
) -> dict[str, str]:
    """
    IMPURE loader (1 call only), but deterministic and cached.

    Responsibilities:
        • Check ConfigState cache
        • Load .env files once
        • Retrieve immutable OS snapshot once
        • Merge deterministically
        • Store in process-local state
    """

    state = ConfigStateManager.instance()

    if state.has_valid_cache(
        root_param=root_param,
        env_file_param=env_file_param,
    ):
        return state.get_env_cache()

    file_env = normalize_env_keys(
        _load_env_files(
            base_dir=resolution.base_dir,
            env_file=resolution.env_file,
        )
    )

    # Remove forbidden/restricted keys (quantum_env must come only from OS)
    for key in RESERVED_ENV_KEYS:
        file_env.pop(key, None)

    os_env = get_frozen_env()  # already normalized, immutable

    # Final merge = user-defined .env overrides OS snapshot
    merged = {**os_env, **file_env}

    effective = extract_application_env(
        merged,
        models=CONFIG_MODELS.models,
        reserved=set(RESERVED_ENV_KEYS),
    )

    state.update(
        base_dir=resolution.base_dir,
        env_file=resolution.env_file,
        env_cache=effective,
        root_param=root_param,
        env_file_param=env_file_param,
    )

    return effective
