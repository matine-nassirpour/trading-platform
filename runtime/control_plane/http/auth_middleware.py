from __future__ import annotations

from aiohttp import web
from runtime.control_plane.auth.auth_port import AdminControlPlaneAuthPort
from runtime.control_plane.auth.models import AdminScope


@web.middleware
async def admin_control_plane_auth_middleware(request: web.Request, handler):
    auth: AdminControlPlaneAuthPort = request.app["admin_auth"]

    principal = auth.authenticate(request.headers.get("Authorization"))
    if principal is None:
        raise web.HTTPUnauthorized(headers={"WWW-Authenticate": "Bearer"})

    request["admin_principal"] = principal
    return await handler(request)


def require_admin_scope(scope: AdminScope):
    async def _guard(request: web.Request):
        principal = request.get("admin_principal")
        if principal is None:
            raise web.HTTPUnauthorized()

        if scope not in principal.scopes:
            raise web.HTTPForbidden(reason="Insufficient scope")

    return _guard
