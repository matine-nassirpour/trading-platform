from __future__ import annotations

from typing import Final

# Reserved environment keys controlled exclusively by the OS.
RESERVED_ENV_KEYS: Final[frozenset[str]] = frozenset(
    {
        "quantum_env",
    }
)
