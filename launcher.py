"""Windows launcher: start the local server and open the browser."""

from __future__ import annotations

import sys
import threading
import time
import webbrowser

START_URL = "http://127.0.0.1:8000/starting"


def _open_browser() -> None:
    time.sleep(1.0)
    webbrowser.open(START_URL)


def main() -> None:
    import uvicorn

    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
