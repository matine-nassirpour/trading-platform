from datetime import UTC, datetime

from aiohttp import web
from runtime.supervisor.adapters.health_adapter import HealthAdapter
from runtime.supervisor.adapters.ready_state_adapter import ReadyStateAdapter
from runtime.supervisor.serializers.canonical_json import canonical_json


def handle_ready_state(request: web.Request) -> web.Response:
    state = ReadyStateAdapter.get_ready_state()
    if state is None:
        payload = {
            "status": "unavailable",
            "reason": "Runtime not READY",
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }
        return web.json_response(payload, status=503)

    canonical = canonical_json(state)
    return web.Response(
        body=canonical.encode("utf-8"),
        content_type="application/json",
        status=200,
    )


def handle_health(request: web.Request) -> web.Response:
    payload = HealthAdapter.get_health()
    return web.json_response(payload, status=200)
