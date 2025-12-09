import requests

from apps.streamlit.config_runtime_client import AdminHTTPConfig, get_admin_http_config


def fetch_ready_config_state() -> tuple[dict | None, AdminHTTPConfig]:
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
        r = requests.get(url, timeout=2)
        data = r.json()
        data["_http_status_code"] = r.status_code
        return data, admin_cfg
    except Exception:
        return None, admin_cfg


def fetch_config_diagnostics(admin_cfg: AdminHTTPConfig) -> dict | None:
    """
    Fetch diagnostics for the configuration state, if available.
    """
    if not admin_cfg.enabled or not admin_cfg.base_url:
        return None

    url = (
        admin_cfg.endpoints.get("config_diagnostics")
        or f"{admin_cfg.base_url}/config-diagnostics"
    )

    try:
        r = requests.get(url, timeout=1)
        return r.json()
    except Exception:
        return None
