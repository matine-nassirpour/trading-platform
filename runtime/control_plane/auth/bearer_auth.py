from __future__ import annotations

import hmac

from typing import Final

from runtime.control_plane.auth.auth_port import AdminControlPlaneAuthPort
from runtime.control_plane.auth.models import AdminPrincipal, AdminScope


class AdminControlPlaneBearerTokenAuth(AdminControlPlaneAuthPort):
    """
    Static bearer-token based authentication.

    - Constant-time comparison
    - Scope-based authorization
    - No external dependencies
    """

    def __init__(
        self,
        *,
        token: str,
        token_id: str = "control_plane",
        scopes: frozenset[AdminScope],
    ) -> None:
        self._token: Final = token
        self._principal: Final = AdminPrincipal(
            token_id=token_id,
            scopes=scopes,
        )

    def authenticate(self, authorization_header: str | None) -> AdminPrincipal | None:
        if not authorization_header:
            return None

        if not authorization_header.startswith("Bearer "):
            return None

        provided = authorization_header.removeprefix("Bearer ").strip()

        if not hmac.compare_digest(provided, self._token):
            return None

        return self._principal
