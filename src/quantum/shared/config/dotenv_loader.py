from __future__ import annotations

import logging
import os
from pathlib import Path

_DOTENV_LOADED = False


def load_dotenv_if_present(
    env_file: str | None = None, override: bool = False
) -> Path | None:
    """
    Loads .env if it exists (once only) and logs the location.

    - override=False: Do not overwrite existing variables (CI/production).
    - override=True: Overrides .env (useful locally occasionally).
    """
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return None

    try:
        from dotenv import find_dotenv, load_dotenv
    except Exception:
        logging.getLogger("config").warning(
            "python-dotenv not installed; .env not loaded"
        )
        return None

    dotenv_path = None
    if env_file:
        p = Path(env_file)
        dotenv_path = p if p.exists() else None
    else:
        # 1) from CWD (classic launch)
        path = find_dotenv(usecwd=True)
        if path:
            dotenv_path = Path(path)
        # 2) fallback: go back from this file (launch via subfolders)
        if not dotenv_path:
            here = Path(__file__).resolve()
            alt = find_dotenv(str(here.parents[3]))
            if alt:
                dotenv_path = Path(alt)

    if dotenv_path and dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path, override=override)
        _DOTENV_LOADED = True
        # Small, non-sensitive snapshot
        snap = {
            "QUANTUM_APP_NAME": os.getenv("QUANTUM_APP_NAME"),
            "QUANTUM_ENV": os.getenv("QUANTUM_ENV"),
            "QUANTUM_TRACE_EXPORTER": os.getenv("QUANTUM_TRACE_EXPORTER"),
            "QUANTUM_METRICS_PORT": os.getenv("QUANTUM_METRICS_PORT"),
        }
        logging.getLogger("config").info(
            "Loaded .env: %s (override=%s)",
            dotenv_path,
            override,
            extra={"attrs": snap},
        )
        return dotenv_path

    logging.getLogger("config").info(f".env not found (cwd={Path.cwd()})")
    return None


def require_env(keys: list[str]) -> None:
    """Fail-fast if required variables are missing."""
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
