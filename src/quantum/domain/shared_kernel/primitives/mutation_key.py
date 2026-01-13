from __future__ import annotations

import secrets


class MutationKey:
    __slots__ = ("_token", "_alive")

    def __init__(self) -> None:
        self._token = secrets.token_hex(32)
        self._alive = True

    def _matches(self, other: MutationKey) -> bool:
        return self._alive and other._alive and self._token == other._token

    def _invalidate(self) -> None:
        self._alive = False
        self._token = "<revoked>"
