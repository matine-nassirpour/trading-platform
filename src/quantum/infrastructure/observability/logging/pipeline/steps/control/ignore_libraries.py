from __future__ import annotations

import logging

from collections.abc import Iterable
from typing import Final

from quantum.infrastructure.observability.logging.pipeline.engine.step import (
    PipelineStep,
)

_DEFAULT_PREFIXES: Final[set[str]] = {
    "urllib3.connectionpool",
    "requests.packages.urllib3.connectionpool",
    "opentelemetry.sdk._logs",
    "opentelemetry.sdk.trace",
    "opentelemetry.sdk.trace.export",
    "opentelemetry.sdk._shared_internal",
}


class _PrefixTrie:
    """High-performance prefix matcher."""

    __slots__ = ("children", "terminal")

    def __init__(self):
        self.children = {}
        self.terminal = False

    def insert(self, prefix: str) -> None:
        node = self
        for ch in prefix:
            node = node.children.setdefault(ch, _PrefixTrie())
        node.terminal = True

    def matches(self, text: str) -> bool:
        node = self
        for ch in text:
            if ch in node.children:
                node = node.children[ch]
                if node.terminal:
                    return True
            else:
                return False
        return node.terminal


class IgnoreLibrariesStep(PipelineStep):
    """Filters out log records from noisy third-party libraries (optimized)."""

    __slots__ = ("_trie",)

    def __init__(self, noisy_prefixes: Iterable[str] | None = None) -> None:
        prefixes = noisy_prefixes or _DEFAULT_PREFIXES
        trie = _PrefixTrie()
        for p in prefixes:
            trie.insert(p)
        self._trie = trie

    def process(self, record: logging.LogRecord) -> bool:
        name = getattr(record, "name", "")
        return not self._trie.matches(name)
