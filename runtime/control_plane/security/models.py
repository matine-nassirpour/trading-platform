from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AdminScope(str, Enum):
    HEALTH = "health"
    METADATA = "metadata"
    CONFIG_DIAGNOSTICS = "config:diagnostics"
    OBSERVABILITY_DIAGNOSTICS = "observability:diagnostics"


@dataclass(frozen=True)
class AdminPrincipal:
    """
    Authenticated control-plane principal.
    Immutable, explicit, auditable.
    """

    token_id: str
    scopes: frozenset[AdminScope]
