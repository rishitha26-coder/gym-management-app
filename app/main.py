"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, SessionLocal, engine, run_migrations
from app.mdns import start_mdns_registration, unregister_mdns_service
from app.network import (
    get_friendly_lan_urls,
    get_lan_ip_url,
    get_lan_url,
    get_server_port,
)
from app.paths import get_static_dir, get_templates_dir, get_uploads_dir, is_frozen
from app.routers import auth, dashboard, members, reports
from app.seed import init_db

templates = Jinja2Templates(directory=str(get_templates_dir()))


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_migrations()
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    start_mdns_registration()
    yield
    unregister_mdns_service()


app = FastAPI(title="Celebrity Fitness Studio", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="local-gym-secret-change-in-prod")

app.mount("/static", StaticFiles(directory=str(get_static_dir())), name="static")
uploads_root = get_uploads_dir().parent
app.mount(
    "/uploads",
    StaticFiles(directory=str(uploads_root)),
    name="uploads",
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(members.router)
app.include_router(reports.router)


@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/health")
async def health(request: Request):
    port = get_server_port(request)
    return {
        "status": "ok",
        "frozen": is_frozen(),
        "port": port,
        "lan_url": get_lan_url(port),
        "lan_urls": get_friendly_lan_urls(port),
        "lan_ip_url": get_lan_ip_url(port),
    }


@app.get("/starting")
async def starting_page(request: Request):
    """Friendly loading page while the local server finishes starting."""
    port = get_server_port(request)
    return templates.TemplateResponse(
        request,
        "starting.html",
        {
            "lan_url": get_lan_url(port),
            "lan_urls": get_friendly_lan_urls(port),
            "lan_ip_url": get_lan_ip_url(port),
        },
    )
