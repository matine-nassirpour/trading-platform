from aiohttp import web
from runtime.control_plane.http.handlers import (
    get_admin_config_diagnostics,
    get_admin_health_status,
    get_admin_observability_diagnostics,
    get_admin_runtime_metadata,
)


def define_admin_http_routes() -> list[web.RouteDef]:
    """
    Declare the HTTP routes exposed by the admin control-plane.

    This function:
    - declares routes only
    - contains no logic
    - performs no side effects
    """

    return [
        web.get("/healthz", get_admin_health_status),
        web.get("/runtime-metadata", get_admin_runtime_metadata),
        web.get("/config-diagnostics", get_admin_config_diagnostics),
        web.get("/observability-diagnostics", get_admin_observability_diagnostics),
    ]
