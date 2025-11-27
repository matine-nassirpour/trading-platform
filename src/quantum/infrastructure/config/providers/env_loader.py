from __future__ import annotations

import logging
import os

from collections.abc import Mapping
from pathlib import Path
from typing import Final

from dotenv import dotenv_values, find_dotenv

from quantum.infrastructure.config.runtime.env_snapshot import get_frozen_env
from quantum.infrastructure.config.runtime.state import ConfigStateManager

LOGGER: Final = logging.getLogger("quantum.config.env_loader")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helpers                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _merge_envs(*layers: Mapping[str, str | None]) -> dict[str, str]:
    """
    Merge environment layers without mutating os.environ.
    Later layers override earlier ones, None values are ignored.
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
        return dotenv_values(base_dir / ".env") or {}

    # --------------------------------------------------------------------------
    # 3. Non-production: layered discovery
    # --------------------------------------------------------------------------
    env_base = dotenv_values(base_dir / ".env") or {}
    env_specific = dotenv_values(base_dir / f".env.{quantum_env}") or {}
    env_local = dotenv_values(base_dir / ".env.local") or {}

    return _merge_envs(env_base, env_specific, env_local)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public API                                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
def load_env(
    root: str | Path | None = None,
    env_file: str | Path | None = None,
) -> dict[str, str]:
    """
    Load environment variables with full immutability and zero side effects.

    - No mutation of os.environ (apply=True is a no-op for safety)
    - Deterministic caching based on (PID, root, env_file)
    - Fully compatible with safety-critical systems
    """

    pid = os.getpid()
    state = ConfigStateManager.instance()

    # --------------------------------------------------------------------------
    # 1. Check cache validity
    # --------------------------------------------------------------------------
    if state.has_valid_cache(root_param=root, env_file_param=env_file):
        cached = state.get_env_cache()
        return cached

    # --------------------------------------------------------------------------
    # 2. Compute new environment set
    # --------------------------------------------------------------------------
    base_dir, resolved_file = _resolve_env_path(root, env_file)
    loaded = _load_from_files(base_dir, resolved_file)

    # Retrieve immutable OS snapshot, lowercased
    frozen_os_env = dict(get_frozen_env())

    # Final merge: .env < .env.{env} < .env.local < OS snapshot
    effective_env = _merge_envs(loaded, frozen_os_env)

    # --------------------------------------------------------------------------
    # 3. Update state with full fingerprint
    # --------------------------------------------------------------------------
    state.update(
        base_dir=base_dir,
        env_file=resolved_file,
        env_cache=effective_env,
        root_param=root,
        env_file_param=env_file,
    )

    LOGGER.info(
        "Environment loaded (immutable)",
        extra={
            "attrs": {
                "base_dir": str(base_dir),
                "env_file": str(resolved_file) if resolved_file else None,
                "env_vars": len(effective_env),
                "applied": False,
                "override": False,
                "pid": pid,
            }
        },
    )

    return effective_env
