"""
Canonical wire-format invariants for all contracts.

RULES:
- All serialized field names on the wire are snake_case.
- No camelCase is allowed on the wire.
- TypeScript adapters are responsible for snake_case → camelCase mapping.
- Python ContractModels always expose snake_case attributes.
"""

import re

_SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def assert_snake_case(name: str) -> None:
    if not _SNAKE_CASE_RE.match(name):
        raise ValueError(
            f"Invalid wire field name {name!r}: "
            "wire format requires strict snake_case"
        )
