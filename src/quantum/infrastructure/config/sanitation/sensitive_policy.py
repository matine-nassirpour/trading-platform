from __future__ import annotations

import re
import unicodedata

from typing import Final

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Canonical Sensitive Semantics                                              │
# │ -------------------------------------------------------------------------- │
# │ LIST RULES:                                                                │
# │   - Vocabulary is semantic, not implementation-dependent.                  │
# │   - All entries MUST represent conceptual secrets identifiable in config.  │
# │   - All entries MUST be lowercase and ASCII-only (normalized downstream).  │
# ╰────────────────────────────────────────────────────────────────────────────╯
GLOBAL_SENSITIVE_PATTERNS: Final[frozenset[str]] = frozenset(
    {
        # Classical credentials
        "password",
        "secret",
        "token",
        "apikey",
        "api_key",
        "credential",
        "credentials",
        "private",
        "access_key",
        "keyid",
        # Authentication mechanisms
        "oauth",
        "jwt",
        "bearer",
        "session",
        "signature",
        "digest",
        "hmac",
        # Practical variations
        "auth",
        "authorization",
        "client_secret",
        "client_key",
        "refresh",
        "id_token",
    }
)

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Boundary-Aware Regex Construction (Industry-Grade)                         │
# │ -------------------------------------------------------------------------- │
# │ Strategy:                                                                  │
# │   - Use custom boundary matcher:                                           │
# │       (?<![A-Za-z0-9])pattern(?![A-Za-z0-9])                               │
# │     → safer than \b for snake_case/hyphens.                                │
# │                                                                            │
# │   - Case-insensitive enforced via (?i).                                    │
# │   - Patterns sorted for deterministic output.                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
_BOUNDARY = r"(?<![A-Za-z0-9])"
_END_BOUNDARY = r"(?![A-Za-z0-9])"

_SENSITIVE_REGEX: Final[re.Pattern[str]] = re.compile(
    rf"(?i){_BOUNDARY}("
    + "|".join(re.escape(p) for p in sorted(GLOBAL_SENSITIVE_PATTERNS))
    + rf"){_END_BOUNDARY}"
)


def _normalize(text: str) -> str:
    """
    Normalize input to NFKC form (defensive normalisation).

    Security rationale:
        - Prevents homoglyph attacks
        - Ensures consistent comparison across input sources (env, JSON, FS)
        - Required in high-assurance systems to avoid malformed key detection
    """
    return unicodedata.normalize("NFKC", text)


def is_sensitive_key(key: str) -> bool:
    """
    Determine whether a configuration key must be treated as sensitive.

    Guarantees:
        • Unicode NFKC normalized
        • Case-insensitive
        • Boundary-aware detection (no false positives from substrings)
        • Deterministic behaviour
        • Zero side effects
    """

    if not isinstance(key, str):
        return False  # Defensive: enforce string semantics

    norm = _normalize(key)
    return _SENSITIVE_REGEX.search(norm) is not None
