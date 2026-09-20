"""
URL validation and SSRF protection.

Dark Shield fetches arbitrary user-supplied URLs, which is a classic SSRF
(Server-Side Request Forgery) risk: an attacker could ask the scanner to reach
`http://169.254.169.254/` (cloud metadata) or `http://localhost:6379`.

Mitigations implemented here:
  * Only http/https schemes are allowed.
  * Hostnames are resolved and every resolved IP is checked against private,
    loopback, link-local, multicast and reserved ranges.
  * Explicit blocklist for localhost-style hostnames.
  * Ports are limited to 80/443/8080/8443 unless a private URL is allowed.
"""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlsplit, urlunsplit

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {80, 443, 8080, 8443}
BLOCKED_HOSTNAMES = {"localhost", "localhost.localdomain", "metadata", "metadata.google.internal", "0.0.0.0"}


@dataclass
class URLValidationResult:
    ok: bool
    url: str = ""
    hostname: str = ""
    error_code: str = ""
    error_message: str = ""
    resolved_ips: Optional[List[str]] = None


def _is_private_ip(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def normalize_url(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return raw
    if "://" not in raw:
        raw = "https://" + raw
    parts = urlsplit(raw)
    host = (parts.hostname or "").lower()
    netloc = host
    if parts.port:
        netloc += f":{parts.port}"
    path = parts.path or "/"
    return urlunsplit((parts.scheme.lower(), netloc, path, parts.query, ""))


def validate_url(raw: str, *, allow_private: bool = False, resolve_dns: bool = True) -> URLValidationResult:
    if not raw or not raw.strip():
        return URLValidationResult(False, error_code="INVALID_URL", error_message="Please enter a website URL.")
    if len(raw) > 2048:
        return URLValidationResult(False, error_code="INVALID_URL", error_message="URL is too long.")

    url = normalize_url(raw)
    try:
        parts = urlsplit(url)
    except ValueError:
        return URLValidationResult(False, error_code="INVALID_URL", error_message="URL could not be parsed.")

    if parts.scheme not in ALLOWED_SCHEMES:
        return URLValidationResult(False, error_code="INVALID_URL", error_message="Only http and https URLs are supported.")

    host = (parts.hostname or "").lower()
    if not host or "." not in host and host != "localhost":
        return URLValidationResult(False, error_code="INVALID_URL", error_message="URL must include a valid domain name.")
    if parts.username or parts.password:
        return URLValidationResult(False, error_code="INVALID_URL", error_message="Credentials in URLs are not allowed.")

    if not allow_private:
        if host in BLOCKED_HOSTNAMES or host.endswith(".local") or host.endswith(".internal"):
            return URLValidationResult(False, error_code="BLOCKED_URL", error_message="Internal or private hosts cannot be analyzed.")
        try:
            port = parts.port
        except ValueError:
            return URLValidationResult(False, error_code="INVALID_URL", error_message="Invalid port.")
        if port and port not in ALLOWED_PORTS:
            return URLValidationResult(False, error_code="BLOCKED_URL", error_message="This port is not allowed.")

        # Literal IP address?
        try:
            if _is_private_ip(host):
                return URLValidationResult(False, error_code="BLOCKED_URL", error_message="Private IP addresses cannot be analyzed.")
            return URLValidationResult(True, url=url, hostname=host, resolved_ips=[host])
        except ValueError:
            pass  # not an IP literal – continue with DNS

        if resolve_dns:
            try:
                infos = socket.getaddrinfo(host, None)
                ips = sorted({info[4][0] for info in infos})
            except socket.gaierror:
                return URLValidationResult(False, error_code="WEBSITE_UNAVAILABLE", error_message="The website domain could not be resolved.")
            for ip in ips:
                if _is_private_ip(ip):
                    return URLValidationResult(False, error_code="BLOCKED_URL", error_message="The website resolves to a private network address.")
            return URLValidationResult(True, url=url, hostname=host, resolved_ips=ips)

    return URLValidationResult(True, url=url, hostname=host)


def website_name(url: str) -> str:
    host = (urlsplit(url).hostname or url).lower()
    return host[4:] if host.startswith("www.") else host
