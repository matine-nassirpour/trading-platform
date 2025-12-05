from aiohttp import web
from runtime.control_plane.admin_http.handlers import (
    handle_config_readiness,
    handle_health,
)


def build_routes() -> list[web.RouteDef]:
    return [
        web.get("/healthz", handle_health),
        web.get("/config-readiness", handle_config_readiness),
    ]
