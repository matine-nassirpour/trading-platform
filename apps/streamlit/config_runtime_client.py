"""
Streamlit-side client for discovering the Quantum Runtime admin HTTP entrypoints.

Improvements (industry-grade):
- Stable Requests session (connection pooling, performance, reliability)
- Strong JSON contract validation (minimal schema)
- Centralized timeout configuration
- No load_dotenv() side-effect at import time (entrypoint must load environment)
- Fully deterministic, read-only API surface
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

HTTP_TIMEOUT_SECONDS = 2.0

_SESSION = requests.Session()


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helper                                                            │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _validate_metadata_payload(
    payload: dict[str, Any],
) -> tuple[str, dict[str, str]] | None:
    """
    Minimal safety-critical schema validation.

    Expected structure:
        {
            "admin_http": {
                "base_url": str,
                "endpoints": { str: str, ... }
            }
        }
    """
    if not isinstance(payload, dict):
        return None

    admin_http = payload.get("admin_http")
    if not isinstance(admin_http, dict):
        return None

    base_url = admin_http.get("base_url")
    if not isinstance(base_url, str) or not base_url:
        return None

    endpoints_raw = admin_http.get("endpoints", {})
    if not isinstance(endpoints_raw, dict):
        endpoints_raw = {}

    endpoints: dict[str, str] = {}
    for k, v in endpoints_raw.items():
        if isinstance(k, str) and isinstance(v, str) and v:
            endpoints[k] = v

    return base_url, endpoints


def _build_default_discovery_url() -> str:
    explicit = os.getenv(DISCOVERY_ENV_VAR)
    if explicit and explicit.strip():
        return explicit.strip()

    host = os.getenv(RUNTIME_HOST_ENV_VAR)
    port = os.getenv(RUNTIME_PORT_ENV_VAR)

    if host and port:
        host = host.strip()
        port = port.strip()
        if host and port:
            return f"http://{host}:{port}/runtime-metadata"

    return DEFAULT_DISCOVERY_URL


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Dataclass                                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
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


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Public API                                                                 │
# ╰────────────────────────────────────────────────────────────────────────────╯
@lru_cache(maxsize=1)
def get_admin_http_config() -> AdminHTTPConfig:
    """
    Discover the Runtime admin HTTP configuration via the `/runtime-metadata` endpoint.

    Discovery strategy:
        1. Use QUANTUM_ADMIN_HTTP_DISCOVERY_URL if set (highest priority).
        2. Otherwise, if QUANTUM_ADMIN_HTTP_HOST and QUANTUM_ADMIN_HTTP_PORT are set,
           build `http://{host}:{port}/runtime-metadata`.
    """
    url = _build_default_discovery_url()

    try:
        resp = _SESSION.get(url, timeout=HTTP_TIMEOUT_SECONDS)
    except Exception:
        # Runtime not reachable, DNS issues, etc.
        return AdminHTTPConfig(enabled=False, base_url=None, endpoints={})

    if resp.status_code != 200:
        # Runtime running but metadata endpoint not healthy / not exposed
        return AdminHTTPConfig(enabled=False, base_url=None, endpoints={})

    try:
        payload = resp.json()
    except Exception:
        # Invalid JSON -> treat as unavailable
        return AdminHTTPConfig(enabled=False, base_url=None, endpoints={})

    validated = _validate_metadata_payload(payload)
    if validated is None:
        return AdminHTTPConfig(enabled=False, base_url=None, endpoints={})

    base_url, endpoints = validated

    return AdminHTTPConfig(enabled=True, base_url=base_url, endpoints=endpoints)
