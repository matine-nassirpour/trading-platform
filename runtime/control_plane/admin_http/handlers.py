from datetime import UTC, datetime

from aiohttp import web
from runtime.control_plane.canonicalization.canonical_json import canonical_json
from runtime.control_plane.diagnostic_providers.config_diagnostics_provider import (
    ConfigDiagnosticsProvider,
)
from runtime.control_plane.diagnostic_providers.config_readiness_provider import (
    ConfigReadinessProvider,
)
from runtime.control_plane.diagnostic_providers.config_state_diagnostics_provider import (
    ConfigStateDiagnosticsProvider,
)
from runtime.control_plane.diagnostic_providers.health_provider import HealthProvider


def handle_config_readiness(request: web.Request) -> web.Response:
    state = ConfigReadinessProvider.get_ready_state()
    canonical = canonical_json(state)

    return web.Response(
        body=canonical.encode("utf-8"),
        content_type="application/json",
        status=200,
    )


def handle_config_diagnostics(request: web.Request) -> web.Response:
    payload = ConfigStateDiagnosticsProvider.as_dict()
    canonical = canonical_json(payload)

    return web.Response(
        body=canonical.encode("utf-8"),
        content_type="application/json",
        status=200,
    )


def handle_full_config_diagnostics(request: web.Request) -> web.Response:
    payload = ConfigDiagnosticsProvider.get_full_diagnostics()
    canonical = canonical_json(payload)
    return web.Response(
        body=canonical.encode("utf-8"),
        content_type="application/json",
        status=200,
    )


def handle_health(request: web.Request) -> web.Response:
    payload = HealthProvider.get_health()
    canonical = canonical_json(payload)
    return web.Response(
        body=canonical.encode("utf-8"),
        content_type="application/json",
        status=200,
    )


def _build_admin_base_url(request: web.Request) -> str:
    """
    Build the effective admin base URL as seen by the client.

    Uses:
        - request.scheme  (http / https)
        - request.host    (host:port from Host header)
        - request.app["admin_base_path"]  (injected by the HTTP server)

    Guarantees:
        - No trailing slash (except for root "/").
    """
    scheme = request.scheme
    host = request.host  # already includes host:port

    base_path = request.app.get("admin_base_path", "/") or "/"
    base_path = base_path.strip()

    if base_path == "" or base_path == "/":
        return f"{scheme}://{host}"

    if not base_path.startswith("/"):
        base_path = "/" + base_path

    if len(base_path) > 1 and base_path.endswith("/"):
        base_path = base_path[:-1]

    return f"{scheme}://{host}{base_path}"


def handle_runtime_metadata(request: web.Request) -> web.Response:
    """
    Expose minimal runtime metadata for external clients (e.g. Streamlit UI).

    This endpoint is the *single source of truth* for:
        - The effective admin HTTP base URL
        - The well-known admin endpoints

    No configuration models are exposed here.
    """
    base_url = _build_admin_base_url(request)

    payload = {
        "status": "ok",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "admin_http": {
            "base_url": base_url,
            "endpoints": {
                "health": f"{base_url}/healthz",
                "config_readiness": f"{base_url}/config-readiness",
                "runtime_metadata": f"{base_url}/runtime-metadata",
                "config_diagnostics": f"{base_url}/config-diagnostics",
                "config_diagnostics_full": f"{base_url}/config-diagnostics-full",
            },
        },
    }

    canonical = canonical_json(payload)
    return web.Response(
        body=canonical.encode("utf-8"),
        content_type="application/json",
        status=200,
    )
