from __future__ import annotations

import re

from collections.abc import Mapping

from pydantic import BaseModel

_PREFIX_RE = re.compile(r"^[a-z0-9]+_$")


def derive_prefixes_from_models(
    models: Mapping[str, type[BaseModel]],
) -> tuple[str, ...]:
    """
    Derive valid environment variable prefixes from model field names.

    Rules (safety-grade):
        • Only consider fields following "<prefix>_<name>"
        • Prefix must match ^[a-z0-9]+_$ (strict POSIX-safe)
        • Deduplicated, sorted deterministically
    """
    prefixes: set[str] = set()

    for model_cls in models.values():
        for field in model_cls.model_fields.keys():
            if "_" not in field:
                continue

            idx = field.find("_") + 1
            prefix = field[:idx]

            if not _PREFIX_RE.fullmatch(prefix):
                raise ValueError(
                    f"Invalid prefix derived from field '{field}': "
                    f"'{prefix}' does not match {_PREFIX_RE.pattern!r}"
                )

            prefixes.add(prefix)

    return tuple(sorted(prefixes))
