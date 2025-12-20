from pathlib import Path

HEADER = """\
// -------------------------------------------------------------------
// AUTO-GENERATED FILE — DO NOT EDIT MANUALLY
// Source of truth: trading-platform/contracts/core/types/json.py
// -------------------------------------------------------------------
"""


JSON_VALUE_TS = """\
/**
 * Canonical JSON value type.
 *
 * Mirrors the backend JsonValue contract exactly.
 *
 * WARNING:
 * - Diagnostics / metadata only
 * - NOT suitable for business logic
 */

export type JsonPrimitive =
  | string
  | number
  | boolean
  | null;

/**
 * Recursive JSON structures.
 *
 * NOTE:
 * TypeScript does NOT allow directly recursive type aliases.
 * This interface exists solely to break the recursion.
 */
export interface JsonComposite {
  readonly [key: string]: JsonValue;
}

/**
 * Canonical JSON value.
 */
export type JsonValue =
  | JsonPrimitive
  | ReadonlyArray<JsonValue>
  | JsonComposite;
"""


def generate_ts_json_value(output_dir: Path) -> Path:
    """
    Generate the canonical JsonValue TypeScript definition.

    This file is:
    - version-agnostic
    - shared across all contract surfaces
    - generated exactly once
    """
    core_dir = output_dir / "shared"
    core_dir.mkdir(parents=True, exist_ok=True)

    output_file = core_dir / "json-value.contract.ts"
    output_file.write_text(
        HEADER + "\n" + JSON_VALUE_TS,
        encoding="utf-8",
    )

    return output_file
