import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Final

try:
    from dotenv import dotenv_values, find_dotenv
except ImportError:
    dotenv_values = None
    find_dotenv = None

_LOGGER: Final = logging.getLogger("config.env")
_LOADED: bool = False
_LAST_BASE_DIR: Path | None = None


def _merge(*layers: Mapping[str, str | None]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for layer in layers:
        for k, v in layer.items():
            if v is not None:
                merged[k] = v
    return merged


def _resolve_base_dir(
    root: str | Path | None, env_file: str | Path | None
) -> tuple[Path | None, Path | None]:
    """
    Returns (base_dir, explicit_env_file).
    - If env_file is provided and exists -> use it (explicit_env_file), base_dir = its parent.
    - Else if root is provided -> base_dir = root (directory), read base_dir/.env
    - Else try to find .env by walking up from CWD (if python-dotenv present).
    """
    if env_file:
        p = Path(env_file)
        if p.exists() and p.is_file():
            return p.parent, p
        # explicit but not found -> treat as not provided; fallback below

    if root:
        return Path(root), None

    if find_dotenv is not None:
        found = find_dotenv(usecwd=True)
        if found:
            fp = Path(found)
            return fp.parent, fp  # note: explicit file discovered
    return Path.cwd(), None


def load_env(
    root: str | Path | None = None,
    *,
    env_file: str | Path | None = None,
    override: bool = False,
) -> Path | None:
    """
    Loads environment variables from .env files (layers).
    Priority: .env < .env.<QUANTUM_ENV> < .env.local < OS variables (if override=False).

    Args:
        root: Project root directory (if known).
        env_file: Explicit path to an .env file to load first as the "base" layer.
        override: If True, overwrites variables already present in os.environ.

    Returns:
        The base directory used, or None if python-dotenv is absent.
    """
    global _LOADED
    global _LAST_BASE_DIR
    if _LOADED:
        return _LAST_BASE_DIR

    if dotenv_values is None:
        _LOGGER.warning("python-dotenv not installed; skipping .env loading")
        return None

    base_dir, explicit_file = _resolve_base_dir(root, env_file)
    if base_dir is None:
        base_dir = Path.cwd()

    # Read the layers
    env_base = (
        dotenv_values(explicit_file)
        if explicit_file
        else dotenv_values(base_dir / ".env")
    )
    current_env = (
        os.getenv("QUANTUM_ENV")
        or (env_base.get("QUANTUM_ENV") if env_base else "")
        or ""
    )

    env_specific = (
        dotenv_values(base_dir / f".env.{current_env}") if current_env else {}
    )
    env_local = dotenv_values(base_dir / ".env.local")

    merged = _merge(env_base or {}, env_specific or {}, env_local or {})

    # Injection into os.environ (with overwrite warning)
    for k, v in merged.items():
        if k in os.environ and not override:
            continue
        if k in os.environ and override:
            # warn (non-sensitive)
            _LOGGER.debug("Overriding existing env var", extra={"attrs": {"key": k}})
        os.environ[k] = v

    _LOADED = True
    _LAST_BASE_DIR = base_dir

    # Logging (non-sensitive)
    snap = {
        "base_dir": str(base_dir),
        "env_file": str(explicit_file) if explicit_file else None,
        "QUANTUM_ENV": os.getenv("QUANTUM_ENV"),
        "QUANTUM_APP_NAME": os.getenv("QUANTUM_APP_NAME"),
        "QUANTUM_TRACE_EXPORTER": os.getenv("QUANTUM_TRACE_EXPORTER"),
        "QUANTUM_METRICS_PORT": os.getenv("QUANTUM_METRICS_PORT"),
        "override": override,
    }
    _LOGGER.info("Environment loaded", extra={"attrs": snap})
    return base_dir


def require_env(keys: list[str]) -> None:
    """Fail-fast if required variables are missing."""
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
