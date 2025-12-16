import logging

from collections.abc import Iterable

from aiohttp import web
from runtime.admin.auth.bearer_auth import AdminControlPlaneBearerTokenAuth
from runtime.admin.auth.models import AdminScope
from runtime.admin.http.auth_middleware import admin_control_plane_auth_middleware
from runtime.admin.http.cors_middleware import admin_control_plane_cors_middleware
from runtime.admin.http.http_forwarding import TrustedProxyPolicy
from runtime.admin.http.routing import define_admin_http_routes

LOGGER = logging.getLogger("quantum.runtime.control_plane.admin_http.server")


def _normalize_base_path(base_path: str) -> str:
    """
    Normalize a base path for use as aiohttp subapp mount point.

    Rules:
        - Empty or "/" → "/"
        - Always starts with "/"
        - No trailing "/" (except for root)
    """
    if not base_path:
        return "/"

    bp = base_path.strip()
    if bp in ("", "/"):
        return "/"

    if not bp.startswith("/"):
        bp = "/" + bp

    # Remove trailing slash, except for root
    if len(bp) > 1 and bp.endswith("/"):
        bp = bp[:-1]

    return bp


def _build_admin_http_app(
    *,
    base_path: str,
    auth_token: str,
    scopes: frozenset[AdminScope],
    trusted_proxy_cidrs: Iterable[str] | None,
) -> web.Application:
    """
    Build the secured admin HTTP application.

    Responsibilities:
        - Install authentication middleware
        - Register authorization backend
        - Register routes only (no logic)
    """
    app = web.Application(
        middlewares=[
            admin_control_plane_cors_middleware(
                allowed_origins={
                    "http://localhost:4200",
                }
            ),
            admin_control_plane_auth_middleware,
        ]
    )

    app["admin_base_path"] = base_path
    app["admin_auth"] = AdminControlPlaneBearerTokenAuth(
        token=auth_token,
        token_id="admin",
        scopes=scopes,
    )

    # Explicit proxy trust policy
    app["trusted_proxy_policy"] = TrustedProxyPolicy(
        allowed_proxies=trusted_proxy_cidrs
    )

    app.add_routes(define_admin_http_routes())
    return app


class AdminHttpControlPlaneServer:
    """
    HTTP-based administrative control-plane adapter.

    Responsibilities:
    - Expose admin endpoints over HTTP
    - Enforce authentication and authorization
    - Integrate with the runtime lifecycle via a control-plane port

    NO business logic
    No lifecycle policy.
    """

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8765,
        base_path: str = "/",
        auth_token: str,
        trusted_proxy_cidrs: Iterable[str] | None = None,
    ) -> None:
        if not auth_token:
            raise ValueError(
                "Admin HTTP auth token must be provided when admin HTTP is enabled"
            )

        self._host = host
        self._port = port
        self._base_path = _normalize_base_path(base_path)
        self._auth_token = auth_token
        self._trusted_proxy_cidrs = (
            tuple(trusted_proxy_cidrs) if trusted_proxy_cidrs else None
        )

        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

    async def start(self) -> None:
        if self._runner is not None:
            LOGGER.warning("[HTTP Server] Admin control-plane server already started.")
            return

        scopes = frozenset(
            {
                AdminScope.HEALTH,
                AdminScope.METADATA,
                AdminScope.CONFIG_DIAGNOSTICS,
                AdminScope.OBSERVABILITY_DIAGNOSTICS,
            }
        )

        root_app = web.Application()

        admin_app = _build_admin_http_app(
            base_path=self._base_path,
            auth_token=self._auth_token,
            scopes=scopes,
            trusted_proxy_cidrs=self._trusted_proxy_cidrs,
        )

        if self._base_path == "/":
            root_app = admin_app
        else:
            root_app.add_subapp(self._base_path, admin_app)

        self._runner = web.AppRunner(root_app)
        await self._runner.setup()

        self._site = web.TCPSite(self._runner, self._host, self._port)
        await self._site.start()

        LOGGER.info(
            "[HTTP Server] Admin control-plane started at http://%s:%s%s",
            self._host,
            self._port,
            "" if self._base_path == "/" else self._base_path,
        )

    async def stop(self) -> None:
        if self._runner is None:
            return

        if self._site is not None:
            await self._site.stop()

        await self._runner.cleanup()
        self._runner = None
        self._site = None

        LOGGER.info("[HTTP Server] Admin control-plane stopped.")


class NullAdminControlPlaneServer:
    """
    No-op admin control-plane implementation.
    Used when the admin control-plane is disabled by configuration.
    """

    @staticmethod
    async def start() -> None:
        LOGGER.info(
            "[HTTP Server] Admin HTTP control-plane is DISABLED by configuration."
        )

    @staticmethod
    async def stop() -> None:
        LOGGER.info(
            "[HTTP Server] Admin HTTP control-plane disabled — nothing to stop."
        )
