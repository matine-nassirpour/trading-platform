from __future__ import annotations

from aiohttp import web
from runtime.control_plane.security.auth_port import AdminAuthPort
from runtime.control_plane.security.models import AdminScope


@web.middleware
async def admin_auth_middleware(request: web.Request, handler):
    auth: AdminAuthPort = request.app["admin_auth"]

    principal = auth.authenticate(request.headers.get("Authorization"))
    if principal is None:
        raise web.HTTPUnauthorized(headers={"WWW-Authenticate": "Bearer"})

    request["admin_principal"] = principal
    return await handler(request)


def require_scope(scope: AdminScope):
    async def _guard(request: web.Request):
        principal = request["admin_principal"]
        if scope not in principal.scopes:
            raise web.HTTPForbidden(reason="Insufficient scope")

    return _guard
