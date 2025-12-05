import logging

from aiohttp import web
from runtime.control_plane.admin_http.routing import build_routes

LOGGER = logging.getLogger("quantum.runtime.http")


class RuntimeSupervisorHTTPServer:
    """
    Minimal, deterministic, low-criticality HTTP server.
    Responsibility: Transport ONLY.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        self._host = host
        self._port = port
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

    async def start(self) -> None:
        if self._runner is not None:
            LOGGER.warning("[HTTP Server] RuntimeSupervisor server already started")
            return

        app = web.Application()
        app.add_routes(build_routes())

        self._runner = web.AppRunner(app)
        await self._runner.setup()

        self._site = web.TCPSite(self._runner, self._host, self._port)
        await self._site.start()

        LOGGER.info(
            f"[HTTP Server] RuntimeSupervisor Server started at http://{self._host}:{self._port}"
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
