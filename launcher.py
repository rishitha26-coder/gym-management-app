"""Windows launcher for Celebrity Fitness Manager: start the local server and open the browser."""

from __future__ import annotations

import socket
import sys
import threading
import time
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


def _open_browser() -> None:
    time.sleep(1.0)
    webbrowser.open(START_URL)


def main() -> None:
    if is_port_in_use(PORT):
        show_error(
            f"Port {PORT} is already in use.\n\n"
            "Celebrity Fitness Manager may already be running — check your browser.\n"
            "If not, close the other program using port 8000 and try again."
        )
        sys.exit(1)

    write_start_bat()
    threading.Thread(target=_open_browser, daemon=True).start()

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        log_level="info",
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
            show_error(f"Could not start Celebrity Fitness Manager:\n\n{exc}")
        sys.exit(1)
    except Exception as exc:
        show_error(f"Could not start Celebrity Fitness Manager:\n\n{exc}")
        sys.exit(1)
