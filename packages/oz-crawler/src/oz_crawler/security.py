from __future__ import annotations

import http.client
import ipaddress
import os
import socket
import ssl
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from urllib.parse import urljoin, urlparse


class UnsafeCrawlerUrl(ValueError):
    pass


class CrawlerFetchError(UnsafeCrawlerUrl):
    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        retry_after: float | None = None,
        transient: bool = False,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after
        self.transient = transient


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
    max_bytes: int | None = None,
    user_agent: str = "oz-crawler/0.1",
    extra_headers: dict[str, str] | None = None,
    attempts: int = 3,
) -> PinnedFetchResponse:
    max_response_bytes = max_bytes if max_bytes is not None else max_page_bytes()
    last_error: CrawlerFetchError | None = None
    for attempt in range(1, max(1, attempts) + 1):
        try:
            response = fetch_public_url_once(
                url,
                timeout=timeout,
                max_redirects=max_redirects,
                max_bytes=max_response_bytes,
                user_agent=user_agent,
                extra_headers=extra_headers,
            )
            return response
        except CrawlerFetchError as exc:
            last_error = exc
            if not exc.transient or attempt >= max(1, attempts):
                raise
            time.sleep(retry_delay(attempt, exc.retry_after))
        except (OSError, TimeoutError) as exc:
            last_error = CrawlerFetchError(str(exc), transient=True)
            if attempt >= max(1, attempts):
                raise last_error from exc
            time.sleep(retry_delay(attempt, None))
    if last_error is not None:
        raise last_error
    raise CrawlerFetchError(f"crawler URL failed: {url}", transient=True)


def fetch_public_url_once(
    url: str,
    *,
    timeout: float,
    max_redirects: int,
    max_bytes: int,
    user_agent: str,
    extra_headers: dict[str, str] | None = None,
) -> PinnedFetchResponse:
    target = resolve_public_fetch_target(url)
    response = fetch_pinned_target(
        target,
        timeout=timeout,
        max_bytes=max_bytes,
        user_agent=user_agent,
        extra_headers=extra_headers,
    )
    if response.status in {301, 302, 303, 307, 308}:
        location = response.headers.get("location")
        if not location:
            return response
        if max_redirects <= 0:
            raise CrawlerFetchError(f"too many redirects while fetching {url}", transient=False)
        return fetch_public_url_once(
            urljoin(url, location),
            timeout=timeout,
            max_redirects=max_redirects - 1,
            max_bytes=max_bytes,
            user_agent=user_agent,
            extra_headers=extra_headers,
        )
    if response.status >= 400:
        retry_after = parse_retry_after(response.headers.get("retry-after"))
        transient = response.status in {408, 425, 429, 500, 502, 503, 504}
        raise CrawlerFetchError(
            f"crawler URL returned HTTP {response.status}: {url}",
            status=response.status,
            retry_after=retry_after,
            transient=transient,
        )
    return response


def fetch_pinned_target(
    target: PublicFetchTarget,
    *,
    timeout: float,
    max_bytes: int,
    user_agent: str,
    extra_headers: dict[str, str] | None = None,
) -> PinnedFetchResponse:
    connection: http.client.HTTPConnection
    if target.https:
        connection = PinnedHTTPSConnection(target, timeout=timeout)
    else:
        connection = PinnedHTTPConnection(target, timeout=timeout)
    try:
        headers = {
            "Host": target.host_header,
            "User-Agent": user_agent,
            "Accept": "text/html, text/markdown, text/plain, application/json, application/yaml, */*;q=0.1",
        }
        headers.update(extra_headers or {})
        connection.request("GET", target.path, headers=headers)
        raw_response = connection.getresponse()
        body = raw_response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise CrawlerFetchError(f"crawler URL exceeded {max_bytes} bytes: {target.url}", transient=False)
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


def max_page_bytes() -> int:
    try:
        return max(1, int(os.environ.get("OZ_MAX_PAGE_BYTES", "2000000")))
    except ValueError:
        return 2_000_000


def parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value.strip()))
    except ValueError:
        return None


def retry_delay(attempt: int, retry_after: float | None) -> float:
    if retry_after is not None:
        return retry_after
    base = 0.35
    try:
        base = max(0.0, float(os.environ.get("OZ_CRAWLER_RETRY_BASE_DELAY_SECONDS", "0.35")))
    except ValueError:
        pass
    return min(8.0, base * (2 ** max(0, attempt - 1)))
