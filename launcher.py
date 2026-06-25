"""Windows launcher for Celebrity Fitness Manager: start the local server and open the browser."""

from __future__ import annotations

import logging
import os
import socket
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

HOST = "0.0.0.0"
PORT = 8000
START_URL = f"http://127.0.0.1:{PORT}/starting"
HEALTH_WAIT_TIMEOUT = 60.0

STARTUP_ERROR = (
    "Could not start Celebrity Fitness Manager.\n\n"
    "Try running as administrator, or allow the app in Windows Security "
    "(Windows Defender / SmartScreen).\n\n"
    "If the problem continues, restart your PC and try again."
)


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def bootstrap_frozen_environment() -> None:
    """Minimal frozen setup before importing app modules (no logging yet)."""
    if not is_frozen():
        return

    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        os.chdir(bundle_root)

    exe_dir = Path(sys.executable).resolve().parent
    for entry in (str(exe_dir), bundle_root):
        if entry and entry not in sys.path:
            sys.path.insert(0, entry)


def setup_startup_logging() -> Path:
    """Configure file logging before any app imports (frozen builds have no console)."""
    from app.paths import get_startup_log_path

    log_path = get_startup_log_path()
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    if not is_frozen():
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)
    return log_path


def configure_frozen_environment() -> None:
    """Log frozen path setup (bootstrap already applied sys.path and cwd)."""
    if not is_frozen():
        return

    bundle_root = getattr(sys, "_MEIPASS", None)
    logging.info("Working directory: %s", os.getcwd())
    if bundle_root:
        logging.info("Bundle root (_MEIPASS): %s", bundle_root)
    logging.info("Executable: %s", sys.executable)


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


def _wait_for_health(timeout: float = 30.0) -> bool:
    """Poll /health until the server responds or timeout expires."""
    health_url = f"http://127.0.0.1:{PORT}/health"
    deadline = time.time() + timeout
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        try:
            with urllib.request.urlopen(health_url, timeout=1.5) as response:
                if response.status == 200:
                    logging.info("/health OK after %s attempt(s)", attempt)
                    return True
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt == 1 or attempt % 10 == 0:
                logging.debug("/health not ready (attempt %s): %s", attempt, exc)
        time.sleep(0.5)
    logging.warning("/health did not respond within %ss (%s attempts)", timeout, attempt)
    return False


def _open_browser_when_ready() -> None:
    """Open the browser only after the server is healthy, or show a timeout hint."""
    from app.paths import get_startup_log_path

    log_path = get_startup_log_path()
    logging.info(
        "Waiting up to %ss for /health before opening browser...",
        HEALTH_WAIT_TIMEOUT,
    )
    if _wait_for_health(timeout=HEALTH_WAIT_TIMEOUT):
        logging.info("Server ready; opening browser at %s", START_URL)
        webbrowser.open(START_URL)
        return

    logging.error("Server not healthy after %ss; opening browser with troubleshooting page", HEALTH_WAIT_TIMEOUT)
    show_error(
        "The app is still starting and may take another minute.\n\n"
        "Your browser will open shortly. If you see a loading screen for more "
        "than 30 seconds, wait and refresh — or click Open Login.\n\n"
        f"If the problem continues, check:\n{log_path}"
    )
    webbrowser.open(START_URL)


def _run_server() -> None:
    """Import the FastAPI app directly and start uvicorn (no string import, no reload)."""
    import uvicorn

    from app.main import app

    logging.info(
        "Starting uvicorn on %s:%s (frozen=%s, cwd=%s)",
        HOST,
        PORT,
        is_frozen(),
        os.getcwd(),
    )
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_config=None,
        access_log=False,
        reload=False,
    )


def main() -> None:
    bootstrap_frozen_environment()
    log_path = setup_startup_logging()
    logging.info("Celebrity Fitness Manager launcher starting")
    logging.info("Python %s on %s", sys.version.replace("\n", " "), sys.platform)
    logging.info("frozen=%s executable=%s", is_frozen(), sys.executable)
    logging.info("startup log: %s", log_path)

    configure_frozen_environment()

    if is_port_in_use(PORT):
        msg = (
            f"Port {PORT} is already in use.\n\n"
            "Celebrity Fitness Manager may already be running — check your browser.\n"
            "If not, close the other program using port 8000 and try again."
        )
        logging.error(msg)
        show_error(msg)
        sys.exit(1)

    logging.info("Port %s is available", PORT)
    write_start_bat()
    logging.info("Launching browser thread (opens after /health is ready)")
    threading.Thread(target=_open_browser_when_ready, daemon=True).start()
    logging.info("Starting uvicorn server...")
    _run_server()


def _format_failure_message(exc: BaseException, log_path: Path) -> str:
    detail = f"{type(exc).__name__}: {exc}"
    return (
        f"{STARTUP_ERROR}\n\n"
        f"Details: {detail}\n\n"
        f"A diagnostic log was saved to:\n{log_path}"
    )


if __name__ == "__main__":
    bootstrap_frozen_environment()
    try:
        from app.paths import get_startup_log_path as _get_log_path

        log_path = _get_log_path()
    except Exception:
        log_path = Path.home() / ".gym-manager" / "startup.log"

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except OSError as exc:
        if not logging.getLogger().handlers:
            try:
                setup_startup_logging()
            except Exception:
                pass
        logging.exception("Launcher failed with OSError")
        if exc.errno in {48, 98, 10048}:  # Address already in use (macOS/Linux/Windows)
            show_error(
                f"Port {PORT} is already in use.\n\n"
                "Close the other program using port 8000 and try again."
            )
        else:
            show_error(_format_failure_message(exc, log_path))
        sys.exit(1)
    except Exception as exc:
        if not logging.getLogger().handlers:
            try:
                setup_startup_logging()
            except Exception:
                pass
        logging.exception("Launcher failed")
        try:
            with log_path.open("a", encoding="utf-8") as log_file:
                log_file.write("\n--- traceback ---\n")
                log_file.write(traceback.format_exc())
        except Exception:
            pass
        show_error(_format_failure_message(exc, log_path))
        sys.exit(1)
