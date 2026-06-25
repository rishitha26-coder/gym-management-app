"""mDNS registration for a friendly .local hostname on the gym LAN."""

from __future__ import annotations

import logging
import socket
import threading

from app.network import DEFAULT_PORT, MDNS_HOSTNAME, get_lan_ip, set_mdns_active

logger = logging.getLogger(__name__)

_zeroconf = None
_service_info = None


def register_mdns_service(port: int = DEFAULT_PORT) -> bool:
    """Register celebrity-fitness.local on the LAN; return True on success."""
    try:
        from zeroconf import ServiceInfo, Zeroconf
    except ImportError:
        logger.info("zeroconf not installed; skipping mDNS registration")
        return False

    ip = get_lan_ip()
    if not ip:
        logger.info("No LAN IP available; skipping mDNS registration")
        return False

    global _zeroconf, _service_info
    try:
        _zeroconf = Zeroconf()
        _service_info = ServiceInfo(
            "_http._tcp.local.",
            "Celebrity Fitness._http._tcp.local.",
            addresses=[socket.inet_aton(ip)],
            port=port,
            properties={},
            server=f"{MDNS_HOSTNAME}.local.",
        )
        _zeroconf.register_service(_service_info)
        set_mdns_active(True)
        logger.info("Registered mDNS hostname http://%s.local:%s", MDNS_HOSTNAME, port)
        return True
    except Exception as exc:
        logger.warning("mDNS registration failed: %s", exc)
        _service_info = None
        if _zeroconf is not None:
            try:
                _zeroconf.close()
            except Exception:
                pass
            _zeroconf = None
        set_mdns_active(False)
        return False


def start_mdns_registration(port: int = DEFAULT_PORT) -> None:
    """Start mDNS registration on a background thread (non-blocking)."""
    from app.paths import is_frozen

    if is_frozen():
        logger.info("Skipping mDNS in frozen build; use computer name URL instead")
        return

    threading.Thread(
        target=register_mdns_service,
        args=(port,),
        name="mdns-register",
        daemon=True,
    ).start()


def unregister_mdns_service() -> None:
    """Best-effort cleanup when the app shuts down."""
    global _zeroconf, _service_info
    if _zeroconf is None or _service_info is None:
        return
    try:
        _zeroconf.unregister_service(_service_info)
        _zeroconf.close()
    except Exception as exc:
        logger.debug("mDNS unregister failed: %s", exc)
    finally:
        _zeroconf = None
        _service_info = None
        set_mdns_active(False)
