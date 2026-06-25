"""Dashboard routes."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import require_login
from app.database import get_db
from app.network import DEFAULT_PORT, get_lan_url
from app.paths import get_templates_dir, get_welcome_dismissed_path, should_show_welcome
from app.schemas import UserOut
from app.services.renewal_service import RenewalService

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory=str(get_templates_dir()))


@router.get("/")
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    stats = RenewalService.get_dashboard_stats(db)
    renewals = RenewalService.get_renewal_lists(db)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "stats": stats,
            "renewals_today": renewals.due_today[:5],
            "renewals_soon": renewals.next_7_days[:5],
            "show_welcome": should_show_welcome(),
            "lan_url": get_lan_url(DEFAULT_PORT),
        },
    )


@router.post("/welcome/dismiss")
async def dismiss_welcome(
    request: Request,
    user: UserOut = Depends(require_login),
):
    get_welcome_dismissed_path().touch()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
