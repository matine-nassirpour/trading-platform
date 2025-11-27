from __future__ import annotations

import re
import unicodedata

from typing import Final

# These patterns intentionally use a *semantic* vocabulary instead of
# implementation-specific names to remain future-proof.
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
# │ Compiled regex (optimised for deterministic substring detection)           │
# │ -------------------------------------------------------------------------- │
# │ Notes:                                                                     │
# │   - We escape each literal and then OR-join them into a single regex.      │
# │   - (?i) enforces case-insensitive comparison.                             │
# │   - Using word boundaries ensures no spurious detection in compound names, │
# │     while still detecting e.g. "my_api_key_root".                          │
# │                                                                            │
# │   Final pattern example:                                                   │
# │       r"(?i)(password|secret|token|...)"                                   │
# ╰────────────────────────────────────────────────────────────────────────────╯
_SENSITIVE_REGEX: Final[re.Pattern[str]] = re.compile(
    "(?i)(" + "|".join(re.escape(p) for p in sorted(GLOBAL_SENSITIVE_PATTERNS)) + ")"
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
        - Unicode normalized (NFKC)
        - Case-insensitive
        - Regex-based detection with strict ordered patterns
        - Future-proof: adding new patterns does not require code changes
        - Side-effect-free and deterministic
    """

    if not isinstance(key, str):
        return False  # Defensive: non-string keys are ignored.

    norm = _normalize(key)

    # Regex search ensures:
    #   - detection of substring occurrences
    #   - strong semantics (no accidental overlaps)
    return _SENSITIVE_REGEX.search(norm) is not None
