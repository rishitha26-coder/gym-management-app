# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Celebrity Fitness Manager Windows build."""

from pathlib import Path

block_cipher = None
project_root = Path(SPECPATH)

datas = [
    (str(project_root / "app" / "templates"), "app/templates"),
    (str(project_root / "app" / "static"), "app/static"),
]

hiddenimports = [
    # FastAPI / Starlette stack
    "app",
    "app.main",
    "app.auth",
    "app.database",
    "app.mdns",
    "app.membership",
    "app.models",
    "app.network",
    "app.paths",
    "app.schemas",
    "app.seed",
    "app.routers",
    "app.routers.auth",
    "app.routers.dashboard",
    "app.routers.members",
    "app.routers.reports",
    "app.services",
    "app.services.member_service",
    "app.services.payment_service",
    "app.services.renewal_service",
    "app.services.report_service",
    "fastapi",
    "fastapi.staticfiles",
    "fastapi.templating",
    "starlette",
    "starlette.middleware.sessions",
    "starlette.routing",
    "starlette.responses",
    "starlette.staticfiles",
    "starlette.templating",
    "jinja2",
    "jinja2.ext",
    "itsdangerous",
    "multipart",
    "python_multipart",
    # Uvicorn and HTTP stack
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.http.httptools_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.protocols.websockets.websockets_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "uvicorn.config",
    "uvicorn.main",
    "uvicorn.server",
    "uvicorn.importer",
    "h11",
    "httptools",
    "websockets",
    "websockets.legacy",
    "websockets.legacy.server",
    # Database
    "sqlalchemy",
    "sqlalchemy.sql.default_comparator",
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.orm",
    "sqlalchemy.engine",
    # Auth / validation / exports
    "bcrypt",
    "pydantic",
    "pydantic_core",
    "openpyxl",
    "reportlab",
    "reportlab.lib",
    "reportlab.platypus",
    # mDNS (bundled but disabled at runtime in frozen exe)
    "zeroconf",
    "zeroconf._handlers",
    "zeroconf._utils.ipaddress",
    "ifaddr",
]

a = Analysis(
    ["launcher.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GymManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GymManager",
)
