from __future__ import annotations

import os

from pathlib import Path

from dotenv import dotenv_values

from quantum.infrastructure.config.environment.snapshot import get_frozen_env
from quantum.infrastructure.config.environment.types import EnvResolutionResult
from quantum.infrastructure.config.runtime.state.config_state import ConfigStateManager


def _load_env_files(base_dir: Path, env_file: Path | None) -> dict[str, str]:
    """
    Load .env and layered non-production files.
    PURE FILE READ ONLY. Does not merge OS env.
    """

    quantum_env = (os.getenv("QUANTUM_ENV") or "dev").strip().lower()
    is_prod = quantum_env == "prod"

    # Explicit file
    if env_file:
        return dotenv_values(env_file) or {}

    # Production strict
    if is_prod:
        return dotenv_values(base_dir / ".env") or {}

    # Non-production layered
    env_base = dotenv_values(base_dir / ".env") or {}
    env_specific = dotenv_values(base_dir / f".env.{quantum_env}") or {}
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
    root_param,
    env_file_param,
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

    file_env = _load_env_files(
        base_dir=resolution.base_dir,
        env_file=resolution.env_file,
    )
    os_env = dict(get_frozen_env())

    # Final merge = user-defined .env overrides OS snapshot
    effective = {**file_env, **os_env}

    state.update(
        base_dir=resolution.base_dir,
        env_file=resolution.env_file,
        env_cache=effective,
        root_param=root_param,
        env_file_param=env_file_param,
    )

    return effective
