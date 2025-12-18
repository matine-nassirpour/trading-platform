from __future__ import annotations

import json
import sys

from collections.abc import Iterable
from pathlib import Path

from contracts.admin_http.v2025_1.config_diagnostics import ConfigDiagnosticsResponse
from contracts.admin_http.v2025_1.health import HealthResponse
from contracts.admin_http.v2025_1.observability_diagnostics import (
    ObservabilityDiagnosticsResponse,
)
from contracts.admin_http.v2025_1.registry import CONTRACT_VERSION, MODELS
from contracts.admin_http.v2025_1.runtime_metadata import RuntimeMetadataResponse
from contracts.core.base import ContractModel
from contracts.generators.json_schema import generate_json_schema

OUTPUT_DIR = Path(f"docs/api/admin_http/v{CONTRACT_VERSION}")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONTRACTS: Iterable[type[ContractModel]] = [
    RuntimeMetadataResponse,
    HealthResponse,
    ConfigDiagnosticsResponse,
    ObservabilityDiagnosticsResponse,
]


def main() -> int:
    for model in MODELS:
        schema = generate_json_schema(model)

        output_file = OUTPUT_DIR / f"{model.__name__}.schema.json"
        output_file.write_text(
            json.dumps(schema, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"[OK] Generated JSON Schema: {output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
