from __future__ import annotations

from typing import Protocol

from runtime.admin.auth.models import AdminPrincipal


class AdminControlPlaneAuthPort(Protocol):
    """
    Authentication and authorization port for the admin control-plane.
    """

    def authenticate(self, authorization_header: str | None) -> AdminPrincipal | None:
        """
        Return an authenticated AdminPrincipal or None if authentication fails.
        Must NEVER raise.
        """
        ...
