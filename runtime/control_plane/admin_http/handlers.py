from datetime import UTC, datetime

from aiohttp import web
from runtime.control_plane.canonicalization.canonical_json import canonical_json
from runtime.control_plane.diagnostic_providers.config_readiness_provider import (
    ConfigReadinessProvider,
)
from runtime.control_plane.diagnostic_providers.health_provider import HealthProvider


def handle_config_readiness(request: web.Request) -> web.Response:
    state = ConfigReadinessProvider.get_ready_state()
    if state is None:
        payload = {
            "status": "unavailable",
            "reason": "Runtime not READY",
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }
        canonical = canonical_json(payload)
        return web.Response(
            body=canonical.encode("utf-8"),
            content_type="application/json",
            status=503,
        )

    canonical = canonical_json(state)
    return web.Response(
        body=canonical.encode("utf-8"),
        content_type="application/json",
        status=200,
    )


def handle_health(request: web.Request) -> web.Response:
    payload = HealthProvider.get_health()
    return web.json_response(payload, status=200)
