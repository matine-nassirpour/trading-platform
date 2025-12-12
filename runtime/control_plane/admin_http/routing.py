from aiohttp import web
from runtime.control_plane.admin_http.handlers import (
    handle_config_diagnostics,
    handle_health,
    handle_observability_diagnostics,
    handle_runtime_metadata,
)


def build_routes() -> list[web.RouteDef]:
    return [
        web.get("/healthz", handle_health),
        web.get("/runtime-metadata", handle_runtime_metadata),
        web.get("/config-diagnostics", handle_config_diagnostics),
        web.get("/observability-diagnostics", handle_observability_diagnostics),
    ]
