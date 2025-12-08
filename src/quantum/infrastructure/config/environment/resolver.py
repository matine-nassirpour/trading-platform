from __future__ import annotations

from pathlib import Path

from dotenv import find_dotenv

from quantum.infrastructure.config.environment.current import is_production
from quantum.infrastructure.config.environment.types import EnvResolutionResult


def _resolve_explicit_env_file(
    env_file: str | Path | None,
) -> EnvResolutionResult | None:
    if not env_file:
        return None

    p = Path(env_file)
    if not p.exists():
        raise FileNotFoundError(f"Explicit env file does not exist: '{p}'")

    return EnvResolutionResult(base_dir=p.parent, env_file=p)


def _resolve_production(root: str | Path | None) -> EnvResolutionResult | None:
    if not is_production():
        return None

    if not root:
        raise RuntimeError(
            "Production requires explicit root or env_file. "
            "Implicit .env discovery forbidden."
        )

    r = Path(root)
    if not r.is_dir():
        raise NotADirectoryError(f"Invalid root directory: '{r}'")

    env_path = r / ".env"
    if not env_path.exists():
        raise FileNotFoundError(
            f"Production expected '{env_path}', but file is missing."
        )

    return EnvResolutionResult(base_dir=r, env_file=env_path)


def _resolve_non_production(root: str | Path | None) -> EnvResolutionResult:
    if root:
        r = Path(root)
        if r.is_dir():
            return EnvResolutionResult(base_dir=r, env_file=None)

    found = find_dotenv(usecwd=True)
    if found:
        fp = Path(found)
        return EnvResolutionResult(base_dir=fp.parent, env_file=fp)

    return EnvResolutionResult(base_dir=Path.cwd(), env_file=None)


def resolve_env(
    *,
    root: str | Path | None = None,
    env_file: str | Path | None = None,
) -> EnvResolutionResult:
    """
    PURE RESOLUTION ONLY.
    No disk reads, no parsing, no loader, no cache.

    Only decide:
        • base directory
        • which .env file (if any) to use
    """

    # 1. Explicit env_file always wins
    explicit = _resolve_explicit_env_file(env_file)
    if explicit:
        return explicit

    # 2. Production: root must be explicit
    prod_res = _resolve_production(root)
    if prod_res:
        return prod_res

    # 3. Non-production implicit discovery allowed
    return _resolve_non_production(root)
