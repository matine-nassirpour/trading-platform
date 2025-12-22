from __future__ import annotations

import ipaddress

from collections.abc import Iterable, Mapping
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
    Defines whether proxy headers are trusted, based on peer IP validation.

    Security guarantees:
    - Headers are trusted ONLY if the request originates from an allowed proxy.
    - Zero trust by default.
    """

    def __init__(self, *, allowed_proxies: Iterable[str] | None = None) -> None:
        self._allowed_networks = (
            frozenset(ipaddress.ip_network(n) for n in allowed_proxies)
            if allowed_proxies
            else frozenset()
        )

    def is_trusted_peer(self, peer_ip: str) -> bool:
        try:
            ip = ipaddress.ip_address(peer_ip)
        except ValueError:
            return False

        return any(ip in net for net in self._allowed_networks)


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


def resolve_admin_http_request_identity(
    *,
    scheme: str,
    host: str,
    headers: Mapping[str, str],
    peer_ip: str,
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

    if not trusted_proxy_policy.is_trusted_peer(peer_ip):
        return ForwardedRequestInfo(scheme=scheme, host=host)

    # RFC 7239 Forwarded
    forwarded = headers.get("Forwarded")
    if forwarded:
        parsed = _parse_forwarded_header(forwarded)
        if "proto" in parsed and "host" in parsed:
            return ForwardedRequestInfo(
                scheme=parsed["proto"],
                host=parsed["host"],
            )

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
