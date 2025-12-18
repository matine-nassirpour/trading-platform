from __future__ import annotations

import sys

from pathlib import Path

from contracts.admin_http.v2025_1.registry import CONTRACT_VERSION, ENUMS, MODELS
from contracts.generators.typescript import generate_ts_interface
from contracts.generators.typescript_enum import generate_ts_enum

OUTPUT_DIR = Path(".generated")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / f"contracts-admin-v{CONTRACT_VERSION}.ts"


def main() -> int:
    lines: list[str] = []

    lines.append(
        "// -------------------------------------------------------------------\n"
        "// AUTO-GENERATED FILE — DO NOT EDIT MANUALLY\n"
        "// Source of truth: trading-platform/contracts/\n"
        "// Regenerate via: make ts-contracts\n"
        "// -------------------------------------------------------------------\n"
    )

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
