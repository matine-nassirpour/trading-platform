import sys

from dataclasses import fields
from enum import Enum
from pathlib import Path
from types import UnionType
from typing import Any, Union, get_args, get_origin

from contracts.generators.typescript.parsers import generate_ts_parser
from contracts.surfaces.admin_http.v2025_1.manifest import CONTRACT_VERSION, MODELS

OUTPUT_DIR = Path(".generated")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / f"contracts-admin-v{CONTRACT_VERSION}.parser.ts"


def _is_optional(tp: Any) -> bool:
    origin = get_origin(tp)
    return (origin is Union or origin is UnionType) and type(None) in get_args(tp)


def main() -> int:
    needs_optional_string = False
    needs_optional_boolean = False
    used_enums: set[type[Enum]] = set()

    # Scan all contracts
    for model in MODELS:
        for f in fields(model):
            tp = f.type
            if _is_optional(tp):
                inner = [a for a in get_args(tp) if a is not type(None)][0]
                if inner is str:
                    needs_optional_string = True
                if inner is bool:
                    needs_optional_boolean = True
            if isinstance(tp, type) and issubclass(tp, Enum):
                used_enums.add(tp)
            if _is_optional(tp):
                inner = [a for a in get_args(tp) if a is not type(None)][0]
                if isinstance(inner, type) and issubclass(inner, Enum):
                    used_enums.add(inner)

    # --------------------------------------------------------------------------
    # Header
    # --------------------------------------------------------------------------
    lines: list[str] = [
        "// -------------------------------------------------------------------\n"
        "// AUTO-GENERATED FILE — DO NOT EDIT MANUALLY\n"
        "// Source of truth: trading-platform/contracts/\n"
        "// Regenerate via: make parsed-ts-contracts\n"
        "// -------------------------------------------------------------------\n\n"
        "/* eslint-disable @typescript-eslint/no-unused-vars */\n"
    ]

    # Contract imports
    contract_names = ",\n  ".join(m.__name__ for m in MODELS)
    lines.append(
        f"import {{\n  {contract_names}\n}} from './contracts-admin-v{CONTRACT_VERSION}';\n"
    )

    # Enum imports
    if used_enums:
        enum_names = ", ".join(
            e.__name__ for e in sorted(used_enums, key=lambda e: e.__name__)
        )
        lines.append(
            f"import {{ {enum_names} }} from './contracts-admin-v{CONTRACT_VERSION}';\n"
        )

    # --------------------------------------------------------------------------
    # Kernel
    # --------------------------------------------------------------------------
    lines.append("""
export class ContractParseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ContractParseError';
  }
}

function expectObject(value: unknown, ctx: string): Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new ContractParseError(`${ctx}: expected object`);
  }
  return value as Record<string, unknown>;
}

function expectString(value: unknown, ctx: string): string {
  if (typeof value !== 'string') {
    throw new ContractParseError(`${ctx}: expected string`);
  }
  return value;
}

function expectBoolean(value: unknown, ctx: string): boolean {
  if (typeof value !== 'boolean') {
    throw new ContractParseError(`${ctx}: expected boolean`);
  }
  return value;
}

function expectRecordOfOptionalString(value: unknown, ctx: string): Readonly<Record<string, string | null>> {
  const o = expectObject(value, ctx);
  const result: Record<string, string | null> = {};

  for (const [k, v] of Object.entries(o)) {
    if (v === null) {
      result[k] = null;
    } else if (typeof v === 'string') {
      result[k] = v;
    } else {
      throw new ContractParseError(`${ctx}: invalid value for key ${k}`);
    }
  }

  return result;
}

function expectRecordOfString(
  value: unknown,
  ctx: string,
): Readonly<Record<string, string>> {
  const o = expectObject(value, ctx);
  const result: Record<string, string> = {};

  for (const [k, v] of Object.entries(o)) {
    if (typeof v !== 'string') {
      throw new ContractParseError(`${ctx}: invalid value for key ${k}`);
    }
    result[k] = v;
  }

  return result;
}

function expectOptionalRecordOfString(
  value: unknown,
  ctx: string,
): Readonly<Record<string, string>> | null {
  if (value === null || value === undefined) {
    return null;
  }
  return expectRecordOfString(value, ctx);
}

function expectNumber(value: unknown, ctx: string): number {
  if (typeof value !== 'number') {
    throw new ContractParseError(`${ctx}: expected number`);
  }
  return value;
}

function expectOptionalNumber(value: unknown, ctx: string): number | null {
  if (value === null || value === undefined) {
    return null;
  }
  return expectNumber(value, ctx);
}

function expectArray<T>(
  value: unknown,
  ctx: string,
  parseItem: (v: unknown, ctx: string) => T,
): ReadonlyArray<T> {
  if (!Array.isArray(value)) {
    throw new ContractParseError(`${ctx}: expected array`);
  }

  return value.map((v, i) => {
    try {
      return parseItem(v, `${ctx}[${i}]`);
    } catch (e) {
      if (e instanceof ContractParseError) {
        throw e;
      }
      throw new ContractParseError(`${ctx}[${i}]: ${String(e)}`);
    }
  });
}


function expectArrayOfString(
  value: unknown,
  ctx: string,
): ReadonlyArray<string> {
  return expectArray(value, ctx, (v, itemCtx) => expectString(v, itemCtx));
}

function expectArrayOfNumber(
  value: unknown,
  ctx: string,
): ReadonlyArray<number> {
  return expectArray(value, ctx, (v, itemCtx) => expectNumber(v, itemCtx));
}

function expectArrayOfBoolean(
  value: unknown,
  ctx: string,
): ReadonlyArray<boolean> {
  return expectArray(value, ctx, (v, itemCtx) => expectBoolean(v, itemCtx));
}

function expectArrayOfEnum<T extends string>(
  value: unknown,
  ctx: string,
  guard: (v: unknown, ctx: string) => T,
): ReadonlyArray<T> {
  return expectArray(value, ctx, (v, itemCtx) => guard(v, itemCtx));
}
""")

    if needs_optional_string:
        lines.append("""
function expectOptionalString(value: unknown, ctx: string): string | null {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value !== 'string') {
    throw new ContractParseError(`${ctx}: expected string or null`);
  }
  return value;
}
""")

    if needs_optional_boolean:
        lines.append("""
function expectOptionalBoolean(value: unknown, ctx: string): boolean | null {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value !== 'boolean') {
    throw new ContractParseError(`${ctx}: expected boolean or null`);
  }
  return value;
}
""")

    # ENUM GUARDS — always generated if enums are used
    for enum in sorted(used_enums, key=lambda e: e.__name__):
        values = " && ".join(f"value !== {repr(member.value)}" for member in enum)
        lines.append(f"""
function expect{enum.__name__}(value: unknown, ctx: string): {enum.__name__} {{
  if (typeof value !== 'string' || ({values})) {{
    throw new ContractParseError(`${{ctx}}: invalid {enum.__name__}`);
  }}
  return value as {enum.__name__};
}}
""")

    # --------------------------------------------------------------------------
    # Parsers
    # --------------------------------------------------------------------------
    for model in MODELS:
        lines.append(generate_ts_parser(model))
        lines.append("")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Generated TypeScript parsers at: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
