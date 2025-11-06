"""
Quantum Observability Schema Generator.

This script generates the canonical JSON schema for `LogPayloadV1`
and writes it to `docs/observability/log_schema_v1.json`.

Purpose
-------
- Provides a machine-readable contract for all structured logs
  emitted by the Quantum platform.
- Ensures schema governance, version traceability, and
  reproducibility across time.
- Designed to be executed both locally and within CI/CD pipelines.

Features
---------
- Loads the `LogPayloadV1` Pydantic model dynamically.
- Exports a fully compliant JSON Schema (draft 2020-12).
- Embeds metadata: generation timestamp, schema version, SHA-256 hash.
- Deterministic output (sorted keys, UTF-8, stable indentation).
"""

from __future__ import annotations

import hashlib
import json
import sys

from datetime import datetime
from importlib import import_module
from pathlib import Path

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Configuration                                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_SCHEMA_PATH = ROOT_DIR / "docs" / "observability" / "log_schema_v1.json"
MODEL_IMPORT_PATH = (
    "src.quantum.infrastructure.observability.logging.models.log_payload_v1"
)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Utilities                                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
def compute_sha256(data: str) -> str:
    """Compute an SHA-256 hash of the given JSON string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def write_pretty_json(path: Path, data: dict) -> None:
    """Write a well-formatted, deterministic JSON document to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Main Generation Routine                                                    │
# ╰────────────────────────────────────────────────────────────────────────────╯
def main() -> None:
    print("[Quantum] Generating LogPayloadV1 schema…")

    try:
        module = import_module(MODEL_IMPORT_PATH)
        model_cls = module.LogPayloadV1
    except Exception as e:
        print(f"[ERROR] Impossible de charger LogPayloadV1 : {e}", file=sys.stderr)
        sys.exit(1)

    # Generate canonical JSON Schema (Pydantic v2)
    schema_dict = model_cls.model_json_schema()
    schema_json = json.dumps(schema_dict, indent=2, ensure_ascii=False, sort_keys=True)
    schema_hash = compute_sha256(schema_json)

    # Governance metadata
    metadata = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "_meta": {
            "generated_at_utc": datetime.utcnow().isoformat() + "Z",
            "model": "LogPayloadV1",
            "schema_version": "1.0",
            "generator": "Quantum Observability Schema Generator",
            "commit_instructions": (
                "Commit this file under version control at docs/observability/log_schema_v1.json"
            ),
            "sha256": schema_hash,
        },
        **schema_dict,
    }

    # Write output file
    write_pretty_json(DOCS_SCHEMA_PATH, metadata)
    print(f"[OK] Schéma généré et sauvegardé dans : {DOCS_SCHEMA_PATH}")
    print(f"[INFO] SHA256 : {schema_hash}")


if __name__ == "__main__":
    main()
