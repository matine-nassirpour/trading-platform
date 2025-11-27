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


def _resolve_explicit_env_file(
    env_file: str | Path | None,
) -> tuple[Path | None, Path | None]:
    """
    Handle explicit env_file parameter.
    Returns (parent_dir, file) if valid, else raises.
    """
    if not env_file:
        return None, None

    p = Path(env_file)
    if not p.exists():
        raise FileNotFoundError(f"Explicit env file does not exist: '{p}'")

    return p.parent, p


def _resolve_production_env_file(root: str | Path | None) -> tuple[Path, Path]:
    """
    Production-grade strict resolution:
        • Only explicit root is allowed
        • Only .env is allowed
        • No autodiscovery
    """
    if not root:
        raise RuntimeError(
            "Production environment requires explicit 'env_file' or explicit 'root'. "
            "Implicit .env discovery is forbidden."
        )

    r = Path(root)
    if not r.is_dir():
        raise NotADirectoryError(f"Specified root is not a directory: '{r}'")

    candidate = r / ".env"
    if not candidate.exists():
        raise FileNotFoundError(
            f"Production environment: expected '{candidate}', but file does not exist."
        )

    return r, candidate


def _resolve_non_production_env_file(
    root: str | Path | None,
) -> tuple[Path, Path | None]:
    """
    Non-production (.env discovery allowed):
        • root → (root, None) if valid
        • autodiscovery via find_dotenv()
        • fallback: CWD
    """
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


def _resolve_env_path(
    root: str | Path | None,
    env_file: str | Path | None,
) -> tuple[Path, Path | None]:
    """
    Resolve base directory + env_file with strict production safety rules.

    Constraints:
        • Production: no implicit discovery (no .env, no .env.local)
        • Production: explicit env_file ONLY (fail-fast otherwise)
        • Non-production: auto-discovery allowed
        • Deterministic and side-effect-free
    """

    # --------------------------------------------------------------------------
    # 1. Explicit env_file always wins (allowed in all environments)
    # --------------------------------------------------------------------------
    explicit_parent, explicit_file = _resolve_explicit_env_file(env_file)
    if explicit_file:
        return explicit_parent, explicit_file

    # --------------------------------------------------------------------------
    # 2. Production-mode strict behaviour
    # --------------------------------------------------------------------------
    quantum_env = (os.getenv("QUANTUM_ENV") or "dev").strip().lower()
    is_production = quantum_env == "prod"

    if is_production:
        return _resolve_production_env_file(root)

    # --------------------------------------------------------------------------
    # 3. Non-production: allow safe auto-discovery (dev/test/staging)
    # --------------------------------------------------------------------------
    return _resolve_non_production_env_file(root)


def _load_from_files(
    base_dir: Path,
    explicit_file: Path | None,
) -> dict[str, str]:
    """
    Load environment variables from disk with production-grade safety rules.
    """

    quantum_env = (os.getenv("QUANTUM_ENV") or "dev").strip().lower()
    is_production = quantum_env == "prod"

    # --------------------------------------------------------------------------
    # 1. Explicit file → always prioritized
    # --------------------------------------------------------------------------
    if explicit_file:
        return dotenv_values(explicit_file) or {}

    # --------------------------------------------------------------------------
    # 2. Production-mode strict loading
    # --------------------------------------------------------------------------
    if is_production:
        # Only `.env` is allowed in production
        env_base = dotenv_values(base_dir / ".env") or {}
        return env_base

    # --------------------------------------------------------------------------
    # 3. Non-production: layered discovery
    # --------------------------------------------------------------------------
    env_base = dotenv_values(base_dir / ".env") or {}

    current_env = os.getenv("QUANTUM_ENV") or env_base.get("QUANTUM_ENV") or "dev"
    env_specific = dotenv_values(base_dir / f".env.{current_env}") or {}
    env_local = dotenv_values(base_dir / ".env.local") or {}

    return _merge_envs(env_base, env_specific, env_local)


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
