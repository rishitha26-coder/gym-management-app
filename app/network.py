"""Local network helpers for LAN access."""

from __future__ import annotations

import socket

DEFAULT_PORT = 8000


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


def get_lan_url(port: int = DEFAULT_PORT) -> str | None:
    """Return the LAN URL staff can use on the same WiFi, or None."""
    ip = get_lan_ip()
    if ip:
        return f"http://{ip}:{port}"
    return None
