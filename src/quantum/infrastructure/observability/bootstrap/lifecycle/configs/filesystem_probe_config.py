from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FileSystemProbeConfig:
    """
    Immutable config describing the behavior of filesystem health checks.

    Used by FileSystemProbe (Protocol).
    """

    deep_probe_enabled: bool = False
