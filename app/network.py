"""Local network helpers for LAN access."""

from __future__ import annotations

import platform
import re
import socket
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.requests import Request

DEFAULT_PORT = 8000
MDNS_HOSTNAME = "celebrity-fitness"

_mdns_active = False


def set_mdns_active(active: bool) -> None:
    """Record whether mDNS registration succeeded (called from app.mdns)."""
    global _mdns_active
    _mdns_active = active


def is_mdns_active() -> bool:
    return _mdns_active


def get_server_port(request: Request | None = None) -> int:
    """Return the port the app is actually served on (from the request when available)."""
    if request is not None and request.url.port:
        return request.url.port
    return DEFAULT_PORT


def sanitize_hostname(name: str) -> str | None:
    """Return a hostname safe to show in a URL, or None if unusable."""
    if not name or not name.strip():
        return None
    host = name.strip().split(".")[0]
    host = re.sub(r"[^\w\-]", "", host, flags=re.ASCII)
    if not host or host.lower() == "localhost":
        return None
    return host


def get_computer_name() -> str | None:
    """Return this PC's network name for LAN URLs."""
    for candidate in (platform.node(), socket.gethostname()):
        if not candidate:
            continue
        sanitized = sanitize_hostname(candidate)
        if sanitized:
            return sanitized
    return None


def get_lan_ip() -> str | None:
    """Return the primary local LAN IPv4 address, or None if unavailable."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
        if ip.startswith("127."):
            return None
        return ip
    except OSError:
        pass

    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127."):
                return ip
    except OSError:
        pass
    return None


def get_friendly_lan_urls(port: int | None = None) -> list[str]:
    """Return friendly LAN URLs staff can use on the same WiFi."""
    if port is None:
        port = DEFAULT_PORT

    urls: list[str] = []

    urls.append(f"http://{MDNS_HOSTNAME}.local:{port}")

    computer_name = get_computer_name()
    if computer_name:
        computer_url = f"http://{computer_name}:{port}"
        if computer_url not in urls:
            urls.append(computer_url)

    return urls


def get_lan_url(port: int | None = None) -> str | None:
    """Return the primary friendly LAN URL, or None if unavailable."""
    urls = get_friendly_lan_urls(port)
    return urls[0] if urls else None


def get_lan_ip_url(port: int | None = None) -> str | None:
    """Return the raw IP LAN URL as a fallback when friendly names fail."""
    if port is None:
        port = DEFAULT_PORT
    ip = get_lan_ip()
    if ip:
        return f"http://{ip}:{port}"
    return None
