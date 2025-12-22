from __future__ import annotations

import sys

from dataclasses import fields
from pathlib import Path
from typing import get_args, get_origin

from contracts.core.types.json import JsonValue
from contracts.generators.typescript.core import generate_ts_json_value
from contracts.generators.typescript.enums import generate_ts_enum
from contracts.generators.typescript.interfaces import generate_ts_interface
from contracts.surfaces.admin_http.v2025_1.manifest import (
    CONTRACT_VERSION,
    ENUMS,
    MODELS,
)

OUTPUT_DIR = Path(".generated")
SURFACE_DIR = OUTPUT_DIR / "control-plane-http" / f"v{CONTRACT_VERSION}"
SURFACE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = SURFACE_DIR / "admin-http.contract.ts"


def _uses_json_value() -> bool:
    for model in MODELS:
        for f in fields(model):
            tp = f.type
            if tp is JsonValue:
                return True
            if get_origin(tp) in (list, dict):
                if JsonValue in get_args(tp):
                    return True
    return False


def main() -> int:
    json_value_file = generate_ts_json_value(OUTPUT_DIR)

    lines: list[str] = [
        "// -------------------------------------------------------------------\n"
        "// AUTO-GENERATED FILE — DO NOT EDIT MANUALLY\n"
        "// Source of truth: trading-platform/contracts/\n"
        "// Regenerate via: make ts-contracts\n"
        "// -------------------------------------------------------------------\n\n"
        "/* eslint-disable @typescript-eslint/no-unused-vars */\n"
    ]

    if _uses_json_value():
        lines.append("import { JsonValue } from '../../shared/json-value.contract';\n")

    for enum in ENUMS:
        lines.append(generate_ts_enum(enum))
        lines.append("")  # spacing

    for model in MODELS:
        lines.append(generate_ts_interface(model))
        lines.append("")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Generated TypeScript contracts at: {OUTPUT_FILE}")
    print(f"[OK] Generated Shared JsonValue at: {json_value_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
