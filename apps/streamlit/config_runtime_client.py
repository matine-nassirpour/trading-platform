"""
Streamlit-side client for discovering the Quantum Runtime admin HTTP entrypoints.

Responsibilities
----------------
- Use the Runtime as the *single source of truth* for all admin HTTP URLs.
- Discover admin HTTP metadata via the `/runtime-metadata` endpoint.
- Expose a minimal, read-only API for Streamlit dashboards.
"""

from __future__ import annotations

import os

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import requests

from dotenv import load_dotenv

load_dotenv()


DISCOVERY_ENV_VAR = "QUANTUM_ADMIN_HTTP_DISCOVERY_URL"
RUNTIME_HOST_ENV_VAR = "QUANTUM_ADMIN_HTTP_HOST"
RUNTIME_PORT_ENV_VAR = "QUANTUM_ADMIN_HTTP_PORT"
DEFAULT_DISCOVERY_URL = "http://127.0.0.1:8765/runtime-metadata"


@dataclass(frozen=True)
class AdminHTTPConfig:
    """
    Runtime-discovered view of the admin HTTP control-plane.

    Fields:
        enabled:
            True  -> metadata successfully discovered and base_url available
            False -> admin HTTP not reachable (runtime down, disabled, or misconfigured)
        base_url:
            The effective admin HTTP base URL (e.g. "http://127.0.0.1:8765" or
            "https://example.com/admin"). None if disabled/unreachable.
        endpoints:
            Mapping of logical endpoint names to fully-qualified URLs.
    """

    enabled: bool
    base_url: str | None
    endpoints: dict[str, str]


def _build_default_discovery_url() -> str:
    explicit = os.getenv(DISCOVERY_ENV_VAR)
    if explicit and explicit.strip():
        return explicit.strip()

    host = os.getenv(RUNTIME_HOST_ENV_VAR)
    port = os.getenv(RUNTIME_PORT_ENV_VAR)

    if host and host.strip() and port and port.strip():
        host = host.strip()
        port = port.strip()
        return f"http://{host}:{port}/runtime-metadata"

    # Fallback
    return DEFAULT_DISCOVERY_URL


@lru_cache(maxsize=1)
def get_admin_http_config() -> AdminHTTPConfig:
    """
    Discover the Runtime admin HTTP configuration via the `/runtime-metadata` endpoint.

    Discovery strategy:
        1. Use QUANTUM_ADMIN_HTTP_DISCOVERY_URL if set (highest priority).
        2. Otherwise, if QUANTUM_ADMIN_HTTP_HOST and QUANTUM_ADMIN_HTTP_PORT are set,
           build `http://{host}:{port}/runtime-metadata`.
    """
    discovery_url = _build_default_discovery_url()

    try:
        response = requests.get(discovery_url, timeout=1)
    except Exception:
        # Runtime not reachable, DNS issues, etc.
        return AdminHTTPConfig(enabled=False, base_url=None, endpoints={})

    if response.status_code != 200:
        # Runtime running but metadata endpoint not healthy / not exposed
        return AdminHTTPConfig(enabled=False, base_url=None, endpoints={})

    try:
        data: dict[str, Any] = response.json()
    except Exception:
        # Invalid JSON -> treat as unavailable
        return AdminHTTPConfig(enabled=False, base_url=None, endpoints={})

    admin_http = data.get("admin_http", {}) or {}
    base_url = admin_http.get("base_url")
    raw_endpoints = admin_http.get("endpoints", {}) or {}

    if not isinstance(base_url, str) or not base_url:
        return AdminHTTPConfig(enabled=False, base_url=None, endpoints={})

    endpoints: dict[str, str] = {}
    if isinstance(raw_endpoints, dict):
        for name, url in raw_endpoints.items():
            if isinstance(name, str) and isinstance(url, str) and url:
                endpoints[name] = url

    return AdminHTTPConfig(
        enabled=True,
        base_url=base_url,
        endpoints=endpoints,
    )
