"""
Generate TypeScript interfaces from Python contracts.

Responsibilities
----------------
- Discover contract models
- Generate deterministic TypeScript interfaces
- Write outputs to a target directory
- Exit non-zero on error

This script is a tooling entrypoint.
It MUST NOT contain contract definitions.
"""

from __future__ import annotations

import sys

from collections.abc import Iterable
from pathlib import Path

from contracts.admin_http.v2025_1.config_diagnostics import ConfigDiagnosticsResponse
from contracts.admin_http.v2025_1.health import HealthResponse
from contracts.admin_http.v2025_1.observability_diagnostics import (
    ObservabilityDiagnosticsResponse,
)
from contracts.admin_http.v2025_1.runtime_metadata import (
    AdminEndpoints,
    AdminHttpDescriptor,
    RuntimeMetadataResponse,
)
from contracts.core.base import ContractModel
from contracts.generators.typescript import generate_ts_interface

OUTPUT_DIR = Path(".generated")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "contracts_admin_v2025_1.ts"

CONTRACTS: Iterable[type[ContractModel]] = [
    AdminEndpoints,
    AdminHttpDescriptor,
    RuntimeMetadataResponse,
    HealthResponse,
    ConfigDiagnosticsResponse,
    ObservabilityDiagnosticsResponse,
]


def main() -> int:
    lines: list[str] = []

    lines.append(
        "// -------------------------------------------------------------------\n"
        "// AUTO-GENERATED FILE — DO NOT EDIT MANUALLY\n"
        "// Source of truth: trading-platform/contracts/\n"
        "// Regenerate via: make contracts-ts\n"
        "// -------------------------------------------------------------------\n"
    )

    for contract in CONTRACTS:
        ts_code = generate_ts_interface(contract)
        lines.append(ts_code)
        lines.append("")  # spacing

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")

    print(f"[OK] Generated temporary TypeScript contracts at: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
