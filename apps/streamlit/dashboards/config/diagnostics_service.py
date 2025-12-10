from collections.abc import Mapping
from typing import Any

from apps.streamlit.config_runtime_client import (
    HTTP_TIMEOUT_SECONDS,
    _SESSION,
    AdminHTTPConfig,
    get_admin_http_config,
)


def fetch_ready_config_state() -> tuple[Mapping[str, Any] | None, AdminHTTPConfig]:
    """
    Fetch the passive read-only READY state from the Runtime.

    Returns:
        (ready_state_payload_or_none, admin_http_config)
    """

    admin_cfg = get_admin_http_config()
    if not admin_cfg.enabled or not admin_cfg.base_url:
        return None, admin_cfg

    url = (
        admin_cfg.endpoints.get("config_readiness")
        or f"{admin_cfg.base_url}/config-readiness"
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
