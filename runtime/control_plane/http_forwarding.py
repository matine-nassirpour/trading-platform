from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ForwardedRequestInfo:
    """
    Canonical client-facing request information,
    resolved via trusted proxy headers.

    This object is SAFE to expose externally.
    """

    scheme: str
    host: str


class TrustedProxyPolicy:
    """
    Defines whether proxy headers are trusted.

    This is an explicit security boundary.
    """

    def __init__(self, *, enabled: bool) -> None:
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled


def _parse_forwarded_header(value: str) -> dict[str, str]:
    """
    Parse RFC 7239 Forwarded header.

    Example:
        Forwarded: proto=https;host=example.com
    """
    result: dict[str, str] = {}

    parts = value.split(";")
    for part in parts:
        if "=" not in part:
            continue
        key, val = part.split("=", 1)
        result[key.strip().lower()] = val.strip().strip('"')

    return result


def resolve_forwarded_request_info(
    *,
    scheme: str,
    host: str,
    headers: Mapping[str, str],
    trusted_proxy_policy: TrustedProxyPolicy,
) -> ForwardedRequestInfo:
    """
    Resolve the effective external-facing scheme + host.

    Resolution order (if proxy is trusted):
        1. RFC 7239 Forwarded
        2. X-Forwarded-Proto / X-Forwarded-Host
        3. Direct request attributes (fallback)

    If proxy is NOT trusted:
        → Always use direct request attributes.
    """

    if not trusted_proxy_policy.enabled:
        return ForwardedRequestInfo(scheme=scheme, host=host)

    # RFC 7239 Forwarded
    forwarded = headers.get("Forwarded")
    if forwarded:
        parsed = _parse_forwarded_header(forwarded)
        proto = parsed.get("proto")
        fwd_host = parsed.get("host")

        if proto and fwd_host:
            return ForwardedRequestInfo(scheme=proto, host=fwd_host)

    # X-Forwarded-*
    xf_proto = headers.get("X-Forwarded-Proto")
    xf_host = headers.get("X-Forwarded-Host")

    if xf_proto and xf_host:
        return ForwardedRequestInfo(
            scheme=xf_proto.split(",")[0].strip(),
            host=xf_host.split(",")[0].strip(),
        )

    # Fallback (direct)
    return ForwardedRequestInfo(scheme=scheme, host=host)
