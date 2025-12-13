import logging

from aiohttp import web
from runtime.admin.auth.bearer_auth import StaticBearerTokenAuth
from runtime.admin.auth.models import AdminScope
from runtime.admin.http.auth_middleware import admin_auth_middleware
from runtime.admin.http.http_forwarding import TrustedProxyPolicy
from runtime.admin.http.routing import build_routes

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


def _build_admin_app(
    *,
    base_path: str,
    auth_token: str,
    scopes: frozenset[AdminScope],
    trust_proxy_headers: bool,
) -> web.Application:
    """
    Build the secured admin HTTP application.

    Responsibilities:
        - Install authentication middleware
        - Register authorization backend
        - Register routes only (no logic)
    """
    app = web.Application(middlewares=[admin_auth_middleware])

    app["admin_base_path"] = base_path
    app["admin_auth"] = StaticBearerTokenAuth(
        token=auth_token,
        token_id="admin",
        scopes=scopes,
    )

    # Explicit proxy trust policy
    app["trusted_proxy_policy"] = TrustedProxyPolicy(enabled=trust_proxy_headers)

    app.add_routes(build_routes())
    return app


class RuntimeSupervisorHTTPServer:
    """
    Minimal, deterministic, secured admin HTTP server.

    Responsibility:
        - HTTP transport only
        - Lifecycle (start/stop)
        - Security enforcement via middleware

    This class contains:
        - NO business logic
        - NO application logic
        - NO domain knowledge
    """

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8765,
        base_path: str = "/",
        auth_token: str,
        trust_proxy_headers: bool = False,
    ) -> None:
        if not auth_token:
            raise ValueError(
                "Admin HTTP auth token must be provided when admin HTTP is enabled"
            )

        self._host = host
        self._port = port
        self._base_path = _normalize_base_path(base_path)
        self._auth_token = auth_token
        self._trust_proxy_headers = trust_proxy_headers

        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

    async def start(self) -> None:
        if self._runner is not None:
            LOGGER.warning("[HTTP Server] RuntimeSupervisor server already started.")
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

        admin_app = _build_admin_app(
            base_path=self._base_path,
            auth_token=self._auth_token,
            scopes=scopes,
            trust_proxy_headers=self._trust_proxy_headers,
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


class NullRuntimeSupervisorHTTPServer:
    """
    No-op implementation for the admin HTTP server.
    Used when the admin HTTP control-plane is disabled by configuration.
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
