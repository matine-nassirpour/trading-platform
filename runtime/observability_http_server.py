from __future__ import annotations

import json
import logging

from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType

from aiohttp import web

from quantum.infrastructure.config.runtime.fsm.model import FSM_SCHEMA_VERSION
from quantum.infrastructure.config.runtime.state.config_state import CONFIG_STATE
from quantum.infrastructure.config.runtime.state.ready_cache import ReadyStateCache

LOGGER = logging.getLogger("quantum.observability.http")


# ---------------------------------------------------------------------------
# Canonical serialization helpers (dependable, certifiable)
# ---------------------------------------------------------------------------


def _normalize_json_safe(value):
    """
    Convert recursively any object into a JSON-serializable structure.

    Handles:
        • MappingProxyType → dict
        • Mapping → dict
        • Path → str
        • Sets/FrozenSets → list
        • Sequences → list
        • Pydantic models → model_dump()
        • Arbitrary objects → vars() / str()
    """
    # None / primitives
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value

    # MappingProxyType (immutable mapping wrapper)
    if isinstance(value, MappingProxyType):
        return {k: _normalize_json_safe(v) for k, v in value.items()}

    # General mappings
    if isinstance(value, Mapping):
        return {str(k): _normalize_json_safe(v) for k, v in value.items()}

    # Sequences / sets → list
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_normalize_json_safe(v) for v in value]

    # Path → str
    if isinstance(value, Path):
        return str(value)

    # Pydantic models
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return _normalize_json_safe(value.model_dump())

    # Generic objects with __dict__
    if hasattr(value, "__dict__"):
        return _normalize_json_safe(vars(value))

    # Fallback safe string
    return str(value)


def _canonical_json(data: object) -> str:
    """
    Produce a canonical JSON representation:
        • All objects normalized to JSON-safe structures
        • Sorted keys (deterministic ordering)
        • Compact separators
        • UTF-8 safe
    """
    normalized = _normalize_json_safe(data)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


# ---------------------------------------------------------------------------
# HTTP Handlers
# ---------------------------------------------------------------------------


async def handle_ready_state(request: web.Request) -> web.Response:
    """
    Expose the FULL READY state of the runtime in canonical JSON form.

    This endpoint is:
    - Read-only
    - Side-effect free
    - Fully deterministic
    - Safe for audit, supervision, regulatory inspection
    """

    state = ReadyStateCache.get()
    fp = ReadyStateCache.get_fingerprint()

    if state is None or fp is None:
        payload = {
            "status": "unavailable",
            "reason": "Runtime is not in READY state.",
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }
        return web.json_response(payload, status=503)

    payload = {
        "schema_version": FSM_SCHEMA_VERSION,
        "fingerprint": fp,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "ready_state": {
            "env": state.env,
            "settings": state.settings,
            "metadata": state.metadata,
        },
        "runtime_snapshot": CONFIG_STATE.snapshot(),
    }

    # canonical string → HTTP response
    canonical = _canonical_json(payload)
    return web.Response(
        body=canonical.encode("utf-8"),
        content_type="application/json",
        charset="utf-8",
        status=200,
    )


async def handle_health(request: web.Request) -> web.Response:
    """
    Minimal liveness endpoint, as expected in all industry systems.
    """
    payload = {
        "status": "ok",
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }
    return web.json_response(payload, status=200)


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------


class ObservabilityHTTPServer:
    """
    Fully async embedded HTTP server exposing observability endpoints.

    Guarantees:
        • Non-blocking
        • Clean Architecture compliant
        • No coupling to runtime internals
        • Read-only access
        • Canonical JSON output
        • Graceful shutdown
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        self._host = host
        self._port = port
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

    # ----------------------------------------------------------------------
    # Start
    # ----------------------------------------------------------------------
    async def start(self) -> None:
        app = web.Application()
        app.add_routes(
            [
                web.get("/ready-state", handle_ready_state),
                web.get("/healthz", handle_health),
            ]
        )

        self._runner = web.AppRunner(app)
        await self._runner.setup()

        self._site = web.TCPSite(self._runner, self._host, self._port)
        await self._site.start()

        LOGGER.info(
            f"Observability HTTP server started at http://{self._host}:{self._port}"
        )

    # ----------------------------------------------------------------------
    # Stop
    # ----------------------------------------------------------------------
    async def stop(self) -> None:
        if self._runner is None:
            return

        LOGGER.info("Stopping Observability HTTP server…")

        if self._site is not None:
            await self._site.stop()

        await self._runner.cleanup()

        self._runner = None
        self._site = None

        LOGGER.info("Observability HTTP server stopped.")
