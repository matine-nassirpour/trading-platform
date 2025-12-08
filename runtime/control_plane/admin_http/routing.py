from aiohttp import web
from runtime.control_plane.admin_http.handlers import (
    handle_config_diagnostics,
    handle_config_readiness,
    handle_fsm_diagnostics,
    handle_full_config_diagnostics,
    handle_health,
    handle_runtime_metadata,
)


def build_routes() -> list[web.RouteDef]:
    return [
        web.get("/healthz", handle_health),
        web.get("/config-readiness", handle_config_readiness),
        web.get("/runtime-metadata", handle_runtime_metadata),
        web.get("/config-diagnostics", handle_config_diagnostics),
        web.get("/config-diagnostics-full", handle_full_config_diagnostics),
        web.get("/fsm-diagnostics", handle_fsm_diagnostics),
    ]
