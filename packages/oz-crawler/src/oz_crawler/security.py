from __future__ import annotations

import ipaddress
import os
import socket
from functools import lru_cache
from urllib.parse import urlparse


class UnsafeCrawlerUrl(ValueError):
    pass


def assert_public_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeCrawlerUrl("crawler URL must be http or https with a host")
    if allow_private_networks():
        return
    host = parsed.hostname.strip().strip("[]")
    for address in resolved_addresses(host):
        if not public_address(address):
            raise UnsafeCrawlerUrl(f"crawler URL resolves to non-public address: {host}")


def public_address(address: str) -> bool:
    parsed = ipaddress.ip_address(address)
    return not (
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_link_local
        or parsed.is_multicast
        or parsed.is_reserved
        or parsed.is_unspecified
    )


@lru_cache(maxsize=2048)
def resolved_addresses(host: str) -> tuple[str, ...]:
    try:
        literal = ipaddress.ip_address(host)
        return (str(literal),)
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeCrawlerUrl(f"crawler URL host could not be resolved: {host}") from exc
    addresses = sorted({info[4][0] for info in infos if info and info[4]})
    if not addresses:
        raise UnsafeCrawlerUrl(f"crawler URL host has no resolved addresses: {host}")
    return tuple(addresses)


def allow_private_networks() -> bool:
    return os.environ.get("OZ_CRAWLER_ALLOW_PRIVATE_NETWORKS", "").lower() in {"1", "true", "yes", "on"}
