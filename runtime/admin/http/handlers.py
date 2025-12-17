from aiohttp import web
from runtime.admin.auth.models import AdminScope
from runtime.admin.contracts.system_status import SystemStatus
from runtime.admin.contracts.version import ADMIN_HTTP_API_VERSION
from runtime.admin.diagnostics.config import ConfigDiagnosticsProvider
from runtime.admin.diagnostics.health import HealthProvider
from runtime.admin.diagnostics.observability import ObservabilityDiagnosticsProvider
from runtime.admin.http.auth_middleware import require_admin_scope
from runtime.admin.http.http_forwarding import (
    TrustedProxyPolicy,
    resolve_admin_http_request_identity,
)
from runtime.contracts.canonical_json import canonical_json
from runtime.lifecycle.system_status_projection import system_status_from_runtime_state

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

    Proxy-aware, deterministic, and secure.
    """

    policy: TrustedProxyPolicy = request.app["trusted_proxy_policy"]

    info = resolve_admin_http_request_identity(
        scheme=request.scheme,
        host=request.host,
        headers=request.headers,
        peer_ip=request.remote or "",
        trusted_proxy_policy=policy,
    )

    base_path = request.app.get("admin_base_path", "/") or "/"
    base_path = base_path.strip()

    if base_path in ("", "/"):
        return f"{info.scheme}://{info.host}"

    if not base_path.startswith("/"):
        base_path = "/" + base_path

    if len(base_path) > 1 and base_path.endswith("/"):
        base_path = base_path[:-1]

    return f"{info.scheme}://{info.host}{base_path}"


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Handlers                                                                   │
# ╰────────────────────────────────────────────────────────────────────────────╯
async def get_admin_runtime_metadata(request: web.Request) -> web.Response:
    """
    Expose minimal runtime metadata for external clients (e.g. Streamlit UI).

    This endpoint is the *single source of truth* for:
        - The effective admin HTTP base URL
        - The well-known admin endpoints

    No configuration models are exposed here.
    """
    await require_admin_scope(AdminScope.METADATA)(request)

    base_url = _build_admin_base_url(request)

    engine = request.app["runtime_engine"]
    system_status: SystemStatus = system_status_from_runtime_state(engine.state)

    payload = {
        "status": system_status.value,
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


async def get_admin_health_status(request: web.Request) -> web.Response:
    await require_admin_scope(AdminScope.HEALTH)(request)

    payload = HealthProvider.get_health()
    return _response(payload, status=200)


async def get_admin_config_diagnostics(request: web.Request) -> web.Response:
    await require_admin_scope(AdminScope.CONFIG_DIAGNOSTICS)(request)

    snapshot = ConfigDiagnosticsProvider.get_snapshot()
    payload = ConfigDiagnosticsProvider.as_dict(snapshot)

    if snapshot.ready:
        return _response(payload, status=200)

    return _response({**payload, "status": "not_ready"}, status=503)


async def get_admin_observability_diagnostics(request: web.Request) -> web.Response:
    await require_admin_scope(AdminScope.OBSERVABILITY_DIAGNOSTICS)(request)

    diagnostics = ObservabilityDiagnosticsProvider.as_dict()

    if diagnostics is None:
        return _response(
            {
                "status": "degraded",
                "reason": "Observability system not initialized",
            },
            status=503,
        )

    return _response(diagnostics, status=200)
