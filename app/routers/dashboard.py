"""Dashboard routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import require_login
from app.database import get_db
from app.paths import get_templates_dir
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
        },
    )
