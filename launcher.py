"""Windows launcher for Celebrity Fitness Manager: start the local server and open the browser."""

from __future__ import annotations

import logging
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

HOST = "0.0.0.0"
PORT = 8000
START_URL = f"http://127.0.0.1:{PORT}/starting"


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def is_port_in_use(port: int) -> bool:
    """Return True when a service is already accepting connections on the port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


STARTUP_ERROR = (
    "Could not start Celebrity Fitness Manager.\n\n"
    "Try running as administrator, or allow the app in Windows Security "
    "(Windows Defender / SmartScreen).\n\n"
    "If the problem continues, restart your PC and try again."
)


def show_error(message: str) -> None:
    """Show a user-visible error (MessageBox on Windows, stderr elsewhere)."""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
                0,
                message,
                "Celebrity Fitness Manager",
                0x10,
            )
        except Exception:
            print(message, file=sys.stderr)
    else:
        print(message, file=sys.stderr)


def write_start_bat() -> None:
    """Create start_gym.bat next to the exe as a manual fallback launcher."""
    if not is_frozen():
        return
    install_dir = Path(sys.executable).resolve().parent
    bat_path = install_dir / "start_gym.bat"
    if bat_path.exists():
        return
    bat_path.write_text(
        "@echo off\r\n"
        "cd /d \"%~dp0\"\r\n"
        "start \"\" \"GymManager.exe\"\r\n",
        encoding="utf-8",
    )


def _wait_for_health(timeout: float = 30.0) -> bool:
    """Poll /health until the server responds or timeout expires."""
    health_url = f"http://127.0.0.1:{PORT}/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=1.5) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(0.5)
    return False


def _open_browser() -> None:
    # Slow PCs may need several seconds before uvicorn accepts connections.
    time.sleep(3.0)
    _wait_for_health(timeout=25.0)
    webbrowser.open(START_URL)


def main() -> None:
    if is_port_in_use(PORT):
        show_error(
            f"Port {PORT} is already in use.\n\n"
            "Celebrity Fitness Manager may already be running — check your browser.\n"
            "If not, close the other program using port 8000 and try again."
        )
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    write_start_bat()
    threading.Thread(target=_open_browser, daemon=True).start()

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        log_level="info",
        log_config=None,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except OSError as exc:
        if exc.errno in {48, 98, 10048}:  # Address already in use (macOS/Linux/Windows)
            show_error(
                f"Port {PORT} is already in use.\n\n"
                "Close the other program using port 8000 and try again."
            )
        else:
            show_error(f"{STARTUP_ERROR}\n\nDetails: {exc}")
        sys.exit(1)
    except Exception as exc:
        show_error(f"{STARTUP_ERROR}\n\nDetails: {exc}")
        sys.exit(1)
