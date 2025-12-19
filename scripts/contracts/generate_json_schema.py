from __future__ import annotations

import json
import sys

from pathlib import Path

from contracts.core.model import ContractModel
from contracts.generators.json_schema.generate import generate_json_schema
from contracts.surfaces.admin_http.v2025_1.manifest import CONTRACT_VERSION, MODELS

OUTPUT_DIR = Path(f"docs/api/admin_http/v{CONTRACT_VERSION}")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    for model in MODELS:
        if not issubclass(model, ContractModel):
            raise TypeError(f"{model!r} is not a ContractModel")

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
