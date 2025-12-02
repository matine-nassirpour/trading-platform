from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IdentityRuntimeBundle:
    """
    Pure Value Object representing the canonical service identity.
    Derives exclusively from validated CoreSettings and is immutable.
    """

    environment: str
    service_namespace: str
    service_name: str
    service_version: str
    instance_id: str
