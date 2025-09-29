import os
from collections.abc import Mapping
from pathlib import Path

try:
    from dotenv import dotenv_values  # type: ignore
except ImportError:  # dev-only dependency may be missing in prod
    dotenv_values = None  # type: ignore[assignment]


def _merge(*layers: Mapping[str, str | None]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for layer in layers:
        for k, v in layer.items():
            if v is not None:
                merged[k] = v
    return merged


def load_local_env(root: str | Path | None = None) -> None:
    """Load .env files into os.environ without overriding existing OS variables."""
    if dotenv_values is None:
        return  # no-op if python-dotenv not installed

    base = Path(root) if root else Path.cwd()

    env_base = dotenv_values(base / ".env")
    # detect current env from OS first, then from base file
    current_env = os.getenv("QUANTUM_ENV") or env_base.get("QUANTUM_ENV") or ""
    env_specific = dotenv_values(base / f".env.{current_env}") if current_env else {}
    env_local = dotenv_values(base / ".env.local")

    # precedence: base < specific < local
    merged = _merge(env_base, env_specific, env_local)

    for k, v in merged.items():
        if k not in os.environ and v is not None:
            os.environ[k] = v
