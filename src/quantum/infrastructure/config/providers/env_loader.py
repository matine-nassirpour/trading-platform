"""
Quantum Core Configuration Environment Loader
─────────────────────────────────────────────
Responsible for discovering, loading, and merging configuration layers
from .env files, local overrides, and runtime environment variables.

Responsibilities
----------------
- Discover .env files relative to a provided root or current working directory.
- Load layered environment files: base, environment-specific, local.
- Merge values deterministically with defined override order.
- Optionally apply values to os.environ (opt-in).
- Maintain consistency and caching through ConfigState.

Design Principles
-----------------
- **Single Responsibility** : loading and merging configuration layers only.
- **Open/Closed** : supports additional providers (e.g., Vault, remote API).
- **No Side Effects by Default** : apply=False preserves purity.
- **Thread Safe** : uses ConfigState for atomic operations.
"""

from __future__ import annotations

import logging
import os

from collections.abc import Mapping
from pathlib import Path
from typing import Final

from quantum.infrastructure.config.runtime.state import ConfigState

try:
    from dotenv import dotenv_values, find_dotenv
except ImportError:
    dotenv_values = None
    find_dotenv = None


_LOGGER: Final = logging.getLogger("quantum.config.env_loader")


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
    root: str | Path | None, env_file: str | Path | None
) -> tuple[Path | None, Path | None]:
    """
    Resolve base directory and .env file path.

    Priority:
        1. Explicit env_file argument (if exists)
        2. Provided root (if directory exists)
        3. Auto-discovery via find_dotenv()
        4. Fallback to current working directory
    """
    if env_file:
        p = Path(env_file)
        if p.exists():
            return p.parent, p

    if root:
        r = Path(root)
        if r.is_dir():
            return r, None

    if find_dotenv is not None:
        found = find_dotenv(usecwd=True)
        if found:
            fp = Path(found)
            return fp.parent, fp

    return Path.cwd(), None


def _load_from_cache(
    state: ConfigState, apply: bool, override: bool
) -> dict[str, str] | None:
    """Return cached environment if valid; apply optionally."""
    if not state.has_valid_cache():
        return None

    cached = state.get_env_cache()
    _LOGGER.debug("Reusing cached environment (pid=%s)", os.getpid())

    if apply:
        _apply_env_vars(cached, apply=True, override=override)
        _LOGGER.debug("Applied cached environment to os.environ (from cache)")

    return cached


def _load_from_files(
    root: str | Path | None, env_file: str | Path | None
) -> tuple[dict[str, str], Path]:
    """Load environment dictionaries from .env files."""
    if dotenv_values is None:
        _LOGGER.warning("python-dotenv not installed; skipping .env loading")
        return dict(os.environ), Path.cwd()

    base_dir, explicit_file = _resolve_env_path(root, env_file)
    base_dir = base_dir or Path.cwd()

    env_base = (
        dotenv_values(explicit_file)
        if explicit_file
        else dotenv_values(base_dir / ".env")
    )
    env_base = env_base or {}

    current_env = os.getenv("QUANTUM_ENV") or env_base.get("QUANTUM_ENV") or "dev"
    env_specific = dotenv_values(base_dir / f".env.{current_env}") or {}
    env_local = dotenv_values(base_dir / ".env.local") or {}

    merged = _merge_envs(env_base, env_specific, env_local)
    return merged, base_dir


def _apply_env_vars(
    envs: Mapping[str, str | None], apply: bool, override: bool
) -> None:
    """
    Apply environment variables to os.environ deterministically.

    :param envs: environment variables to apply.
    """
    if not apply:
        return

    for k, v in envs.items():
        if v is None:
            continue
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
    Load environment variables from .env files in a process-safe way.

    Design goals:
        - Deterministic and reproducible merging.
        - Thread/process safety via ConfigState.
        - Zero side effects unless apply=True.

    Args:
        root: optional project root or base directory.
        env_file: optional explicit .env file path.
        override: if True, overrides existing os.environ keys.
        apply: if True, applies merged values to os.environ (opt-in).

    Returns:
        dict[str, str]: merged environment variables.
    """
    pid = os.getpid()
    state = ConfigState.instance()

    def _execute_load() -> dict[str, str]:
        cached = _load_from_cache(state, apply, override)
        if cached is not None:
            return cached

        merged, base_dir = _load_from_files(root, env_file)
        _apply_env_vars(merged, apply, override)

        state.update(base_dir=base_dir, loaded_pid=pid, env_cache=merged)
        _LOGGER.info(
            "Environment loaded",
            extra={
                "attrs": {
                    "base_dir": str(base_dir),
                    "env": os.getenv("QUANTUM_ENV", merged.get("QUANTUM_ENV", "dev")),
                    "applied": apply,
                    "override": override,
                }
            },
        )
        return merged

    # Execute atomically under internal lock
    return state.access(_execute_load)
