from __future__ import annotations

import http.client
import ipaddress
import os
import socket
import ssl
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from urllib.parse import urljoin, urlparse


class UnsafeCrawlerUrl(ValueError):
    pass


@dataclass(frozen=True)
class PinnedFetchResponse:
    url: str
    body: bytes
    headers: dict[str, str]
    status: int


@dataclass(frozen=True)
class PublicFetchTarget:
    url: str
    host: str
    port: int
    address: str
    host_header: str
    path: str
    https: bool


def assert_public_http_url(url: str) -> None:
    resolve_public_fetch_target(url)


def resolve_public_fetch_target(url: str) -> PublicFetchTarget:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeCrawlerUrl("crawler URL must be http or https with a host")
    host = parsed.hostname.strip().strip("[]")
    addresses = resolved_addresses(host)
    if not allow_private_networks():
        for address in addresses:
            if not public_address(address):
                raise UnsafeCrawlerUrl(f"crawler URL resolves to non-public address: {host}")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    host_header = host
    if parsed.port and parsed.port not in {80, 443}:
        host_header = f"{host}:{parsed.port}"
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return PublicFetchTarget(
        url=url,
        host=host,
        port=port,
        address=addresses[0],
        host_header=host_header,
        path=path,
        https=parsed.scheme == "https",
    )


def fetch_public_url(
    url: str,
    *,
    timeout: float = 20,
    max_redirects: int = 3,
    max_bytes: int = 8 * 1024 * 1024,
    user_agent: str = "oz-crawler/0.1",
) -> PinnedFetchResponse:
    target = resolve_public_fetch_target(url)
    response = fetch_pinned_target(target, timeout=timeout, max_bytes=max_bytes, user_agent=user_agent)
    if response.status in {301, 302, 303, 307, 308}:
        location = response.headers.get("location")
        if not location:
            return response
        if max_redirects <= 0:
            raise UnsafeCrawlerUrl(f"too many redirects while fetching {url}")
        return fetch_public_url(
            urljoin(url, location),
            timeout=timeout,
            max_redirects=max_redirects - 1,
            max_bytes=max_bytes,
            user_agent=user_agent,
        )
    if response.status >= 400:
        raise UnsafeCrawlerUrl(f"crawler URL returned HTTP {response.status}: {url}")
    return response


def fetch_pinned_target(
    target: PublicFetchTarget,
    *,
    timeout: float,
    max_bytes: int,
    user_agent: str,
) -> PinnedFetchResponse:
    connection: http.client.HTTPConnection
    if target.https:
        connection = PinnedHTTPSConnection(target, timeout=timeout)
    else:
        connection = PinnedHTTPConnection(target, timeout=timeout)
    try:
        connection.request(
            "GET",
            target.path,
            headers={
                "Host": target.host_header,
                "User-Agent": user_agent,
                "Accept": "text/html, text/markdown, text/plain, application/json, application/yaml, */*;q=0.1",
            },
        )
        raw_response = connection.getresponse()
        body = raw_response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise UnsafeCrawlerUrl(f"crawler URL exceeded {max_bytes} bytes: {target.url}")
        return PinnedFetchResponse(
            url=target.url,
            body=body,
            headers={key.lower(): value for key, value in raw_response.getheaders()},
            status=int(raw_response.status),
        )
    finally:
        connection.close()


class PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, target: PublicFetchTarget, *, timeout: float) -> None:
        super().__init__(target.address, port=target.port, timeout=timeout)
        self._target = target


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, target: PublicFetchTarget, *, timeout: float) -> None:
        super().__init__(target.address, port=target.port, timeout=timeout, context=ssl.create_default_context())
        self._target = target

    def connect(self) -> None:
        sock = socket.create_connection((self._target.address, self._target.port), self.timeout, self.source_address)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        context: Any = self._context
        self.sock = context.wrap_socket(sock, server_hostname=self._target.host)


def pinned_fetch_required() -> bool:
    if allow_private_networks():
        return False
    if os.environ.get("OZ_CRAWLER_ALLOW_UNPINNED_FETCHERS", "").lower() in {"1", "true", "yes", "on"}:
        return False
    return os.environ.get("OZ_ENV", "").lower() in {"prod", "production"}


def public_crawl_url(url: str) -> bool:
    try:
        assert_public_http_url(url)
        return True
    except UnsafeCrawlerUrl:
        return False


def public_address(address: str) -> bool:
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError:
        return False
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
