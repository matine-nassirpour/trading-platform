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

    def __post_init__(self):
        if not self.environment:
            raise ValueError("IdentityBundle.environment must be non-empty.")

        if not self.service_namespace:
            raise ValueError("IdentityBundle.service_namespace must be non-empty.")

        if not self.service_name:
            raise ValueError("IdentityBundle.service_name must be non-empty.")

        if not self.service_version:
            raise ValueError("IdentityBundle.service_version must be non-empty.")

        if not self.instance_id:
            raise ValueError("IdentityBundle.instance_id must be non-empty.")

        # Normalizations
        object.__setattr__(self, "environment", str(self.environment).strip().lower())
