from aiohttp import web
from runtime.control_plane.canonicalization.canonical_json import canonical_json
from runtime.control_plane.diagnostic_providers.config_diagnostics_provider import (
    ConfigDiagnosticsProvider,
)
from runtime.control_plane.diagnostic_providers.health_provider import HealthProvider
from runtime.control_plane.diagnostic_providers.observability_diagnostics_provider import (
    ObservabilityDiagnosticProvider,
)
from runtime.control_plane.version import ADMIN_HTTP_API_VERSION

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helpers                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _response(payload: dict, status: int = 200) -> web.Response:
    canonical = canonical_json(payload)
    return web.Response(
        body=canonical.encode("utf-8"),
        content_type="application/json",
        headers=NO_CACHE_HEADERS,
        status=status,
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
    host = request.host

    base_path = request.app.get("admin_base_path", "/") or "/"
    base_path = base_path.strip()

    if base_path in ("", "/"):
        return f"{scheme}://{host}"

    if not base_path.startswith("/"):
        base_path = "/" + base_path

    if len(base_path) > 1 and base_path.endswith("/"):
        base_path = base_path[:-1]

    return f"{scheme}://{host}{base_path}"


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Handlers                                                                   │
# ╰────────────────────────────────────────────────────────────────────────────╯
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
        "api_version": ADMIN_HTTP_API_VERSION,
        "admin_http": {
            "base_url": base_url,
            "endpoints": {
                "health": f"{base_url}/healthz",
                "runtime_metadata": f"{base_url}/runtime-metadata",
                "config_diagnostics": f"{base_url}/config-diagnostics",
                "observability_diagnostics": f"{base_url}/observability-diagnostics",
            },
        },
    }

    return _response(payload, status=200)


def handle_health(request: web.Request) -> web.Response:
    payload = HealthProvider.get_health()
    return _response(payload, status=200)


def handle_config_diagnostics(request: web.Request) -> web.Response:
    snapshot = ConfigDiagnosticsProvider.get_snapshot()
    payload = ConfigDiagnosticsProvider.as_dict(snapshot)

    if snapshot.ready:
        return _response(payload, status=200)

    # Not ready → Service Unavailable
    return _response(
        {
            **payload,
            "status": "not_ready",
        },
        status=503,
    )


def handle_observability_diagnostics(request: web.Request) -> web.Response:
    diag = ObservabilityDiagnosticProvider.as_dict()

    if diag is None:
        return _response(
            {
                "status": "degraded",
                "reason": "Observability system not initialized",
            },
            status=503,
        )

    return _response(diag, status=200)
