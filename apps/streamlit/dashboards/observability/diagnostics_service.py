from collections.abc import Mapping
from typing import Any

from apps.streamlit.config_runtime_client import (
    HTTP_TIMEOUT_SECONDS,
    _SESSION,
    AdminHTTPConfig,
    get_admin_http_config,
)


def fetch_observability_diagnostics() -> (
    tuple[Mapping[str, Any] | None, AdminHTTPConfig]
):
    """
    Fetch the Observability diagnostic snapshot from RuntimeSupervisor.

    Returns:
        (diagnostic_payload_or_none, admin_http_config)
    """

    admin_cfg = get_admin_http_config()
    if not admin_cfg.enabled or not admin_cfg.base_url:
        return None, admin_cfg

    url = (
        admin_cfg.endpoints.get("observability_diagnostics")
        or f"{admin_cfg.base_url}/observability-diagnostics"
    )

    try:
        r = _SESSION.get(url, timeout=HTTP_TIMEOUT_SECONDS)
    except Exception:
        return None, admin_cfg

    try:
        payload = r.json()
    except Exception:
        return None, admin_cfg

    # Never mutate original payload → create attached metadata
    payload = dict(payload)
    payload["_http_status_code"] = r.status_code

    return payload, admin_cfg
