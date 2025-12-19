// -------------------------------------------------------------------
// AUTO-GENERATED FILE — DO NOT EDIT MANUALLY
// Source of truth: trading-platform/contracts/core/types/json.py
// -------------------------------------------------------------------

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
