"""Application paths for development and frozen (PyInstaller) runs."""

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """Return True when running as a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def _bundle_root() -> Path:
    """Root directory for bundled read-only assets."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return Path(__file__).resolve().parent.parent


def _user_data_root() -> Path:
    """Persistent user data directory (database, uploads)."""
    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        return Path(app_data) / "GymManager"
    return Path.home() / ".gym-manager"


def get_project_root() -> Path:
    """Project root in dev mode; bundle root when frozen."""
    return _bundle_root()


def get_data_dir() -> Path:
    """Directory for SQLite database files."""
    if is_frozen():
        data_dir = _user_data_root() / "data"
    else:
        data_dir = _bundle_root()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_database_path() -> Path:
    """Full path to the SQLite database file."""
    return get_data_dir() / "gym.db"


def get_uploads_dir() -> Path:
    """Directory for member photo uploads."""
    if is_frozen():
        uploads_dir = _user_data_root() / "uploads" / "members"
    else:
        uploads_dir = _bundle_root() / "uploads" / "members"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return uploads_dir


def get_templates_dir() -> Path:
    """Jinja2 templates directory."""
    return _bundle_root() / "app" / "templates"


def get_static_dir() -> Path:
    """Static assets directory."""
    return _bundle_root() / "app" / "static"


def uploads_url_prefix() -> str:
    """URL path prefix served for uploaded member photos."""
    return "/uploads/members"
