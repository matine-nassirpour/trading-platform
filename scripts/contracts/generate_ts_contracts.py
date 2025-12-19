from __future__ import annotations

import sys

from pathlib import Path

from contracts.generators.typescript.enums import generate_ts_enum
from contracts.generators.typescript.interfaces import generate_ts_interface
from contracts.surfaces.admin_http.v2025_1.manifest import (
    CONTRACT_VERSION,
    ENUMS,
    MODELS,
)

OUTPUT_DIR = Path(".generated")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / f"contracts-admin-v{CONTRACT_VERSION}.ts"


def main() -> int:
    lines: list[str] = [
        "// -------------------------------------------------------------------\n"
        "// AUTO-GENERATED FILE — DO NOT EDIT MANUALLY\n"
        "// Source of truth: trading-platform/contracts/\n"
        "// Regenerate via: make ts-contracts\n"
        "// -------------------------------------------------------------------\n\n"
        "/* eslint-disable @typescript-eslint/no-unused-vars */\n"
    ]

    for enum in ENUMS:
        lines.append(generate_ts_enum(enum))
        lines.append("")  # spacing

    for model in MODELS:
        lines.append(generate_ts_interface(model))
        lines.append("")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Generated TypeScript contracts at: {OUTPUT_FILE}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
