from __future__ import annotations

import secrets


class MutationKey:
    __slots__ = ("_token",)

    def __init__(self) -> None:
        self._token = secrets.token_hex(32)

    def _matches(self, other: MutationKey) -> bool:
        return self._token == other._token
