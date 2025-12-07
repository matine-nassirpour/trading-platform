import logging

from aiohttp import web
from runtime.control_plane.admin_http.routing import build_routes

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
    if bp == "" or bp == "/":
        return "/"

    if not bp.startswith("/"):
        bp = "/" + bp

    # Remove trailing slash, except for root
    if len(bp) > 1 and bp.endswith("/"):
        bp = bp[:-1]

    return bp


class RuntimeSupervisorHTTPServer:
    """
    Minimal, deterministic, low-criticality HTTP server.
    Responsibility: Transport ONLY.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        base_path: str = "/",
    ) -> None:
        self._host = host
        self._port = port
        self._base_path = _normalize_base_path(base_path)

        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

    async def start(self) -> None:
        if self._runner is not None:
            LOGGER.warning("[HTTP Server] RuntimeSupervisor server already started.")
            return

        app = web.Application()
        # Expose the normalized base path for handlers that need to build URLs.
        app["admin_base_path"] = self._base_path

        routes = build_routes()

        if self._base_path == "/":
            app.add_routes(routes)
        else:
            subapp = web.Application()
            subapp["admin_base_path"] = self._base_path
            subapp.add_routes(routes)
            app.add_subapp(self._base_path, subapp)

        self._runner = web.AppRunner(app)
        await self._runner.setup()

        self._site = web.TCPSite(self._runner, self._host, self._port)
        await self._site.start()

        LOGGER.info(
            "[HTTP Server] RuntimeSupervisor Server started at http://%s:%s%s",
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

        LOGGER.info("[HTTP Server] RuntimeSupervisor server stopped.")


class NullRuntimeSupervisorHTTPServer:
    """
    No-op implementation for the admin HTTP server.

    Used when the admin HTTP entrypoint is disabled via configuration.
    Satisfies the AdminHTTPServerPort protocol expected by RuntimeEngine.
    """

    @staticmethod
    async def start() -> None:
        LOGGER.info(
            "[HTTP Server] Admin HTTP server is DISABLED by configuration. "
            "No HTTP control-plane will be exposed."
        )

    @staticmethod
    async def stop() -> None:
        LOGGER.info("[HTTP Server] Admin HTTP server disabled — nothing to stop.")
