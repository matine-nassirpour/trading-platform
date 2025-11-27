from __future__ import annotations

import logging
import os

from collections.abc import Mapping
from pathlib import Path
from typing import Final

from dotenv import dotenv_values, find_dotenv

from quantum.infrastructure.config.runtime.state import ConfigState

LOGGER: Final = logging.getLogger("quantum.config.env_loader")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helpers                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _merge_envs(*layers: Mapping[str, str | None]) -> dict[str, str]:
    """
    Merge multiple environment layers, ignoring None values.
    Later layers override earlier ones.
    """
    merged: dict[str, str] = {}
    for layer in layers:
        for k, v in layer.items():
            if v is not None:
                merged[k] = v
    return merged


def _resolve_env_path(
    root: str | Path | None,
    env_file: str | Path | None,
) -> tuple[Path, Path | None]:
    """Resolve base directory + explicit env_file if provided."""

    # 1. Explicit env_file
    if env_file:
        p = Path(env_file)
        if p.exists():
            return p.parent, p

    # 2. root directory
    if root:
        r = Path(root)
        if r.is_dir():
            return r, None

    # 3. Auto-discovery
    if find_dotenv is not None:
        found = find_dotenv(usecwd=True)
        if found:
            fp = Path(found)
            return fp.parent, fp

    # 4. Fallback
    return Path.cwd(), None


def _load_from_files(
    base_dir: Path,
    explicit_file: Path | None,
) -> dict[str, str]:
    """Load environment layers from disk."""

    if explicit_file:
        env_base = dotenv_values(explicit_file)
    else:
        env_base = dotenv_values(base_dir / ".env")

    env_base = env_base or {}

    current_env = os.getenv("QUANTUM_ENV") or env_base.get("QUANTUM_ENV") or "dev"
    env_specific = dotenv_values(base_dir / f".env.{current_env}") or {}
    env_local = dotenv_values(base_dir / ".env.local") or {}

    merged = _merge_envs(env_base, env_specific, env_local)
    return merged


def _apply_env_vars(envs: Mapping[str, str], *, apply: bool, override: bool) -> None:
    if not apply:
        return
    for k, v in envs.items():
        if not override and k in os.environ:
            continue
        os.environ[k] = v


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Core Loader                                                                │
# ╰────────────────────────────────────────────────────────────────────────────╯
def load_env(
    root: str | Path | None = None,
    env_file: str | Path | None = None,
    *,
    override: bool = False,
    apply: bool = False,
) -> dict[str, str]:
    """
    Load environment variables with deterministic, parameter-based caching.

    Cache invalidation depends **only** on:
        • the current PID
        • the `root` parameter
        • the `env_file` parameter

    Changes to `.env` files on disk do **not** invalidate the cache.

    On cache miss:
        • resolve base directory / env file
        • load .env → .env.{QUANTUM_ENV} → .env.local
        • merge layers
        • optionally apply to os.environ

    This design ensures reproducible, explicit, and side-effect-free environment
    loading suitable for safety-grade and production-grade systems.
    """

    pid = os.getpid()
    state = ConfigState.instance()

    # --------------------------------------------------------------------------
    # 1. Check cache validity w.r.t parameters
    # --------------------------------------------------------------------------
    if state.has_valid_cache(
        root_param=root,
        env_file_param=env_file,
    ):
        cached = state.get_env_cache()
        if apply:
            _apply_env_vars(cached, apply=True, override=override)

        LOGGER.debug(
            "Reusing cached environment for PID=%s (root=%s, env_file=%s)",
            pid,
            root,
            env_file,
        )
        return cached

    # --------------------------------------------------------------------------
    # 2. Load from underlying files
    # --------------------------------------------------------------------------
    base_dir, resolved_file = _resolve_env_path(root, env_file)
    merged = _load_from_files(base_dir, resolved_file)

    _apply_env_vars(merged, apply=apply, override=override)

    # --------------------------------------------------------------------------
    # 3. Update state with full fingerprint
    # --------------------------------------------------------------------------
    state.update(
        base_dir=base_dir,
        env_file=resolved_file,
        env_cache=merged,
        loaded_pid=pid,
        root_param=root,
        env_file_param=env_file,
    )

    LOGGER.info(
        "Environment loaded",
        extra={
            "attrs": {
                "base_dir": str(base_dir),
                "env_file": str(resolved_file) if resolved_file else None,
                "root_param": str(root),
                "env_file_param": str(env_file),
                "applied": apply,
                "override": override,
                "env_vars": len(merged),
            }
        },
    )

    return merged
