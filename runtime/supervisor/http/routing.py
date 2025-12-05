from aiohttp import web
from runtime.supervisor.http.handlers import handle_health, handle_ready_state


def build_routes() -> list[web.RouteDef]:
    return [
        web.get("/healthz", handle_health),
        web.get("/ready-state", handle_ready_state),
    ]
