"""Dashboard routes."""

from datetime import date

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import require_login
from app.database import get_db
from app.models import Member, MemberStatus, UserRole
from app.services.member_service import MemberService
from app.network import get_lan_url, get_server_port
from app.paths import (
    get_lan_dismissed_path,
    get_templates_dir,
    get_welcome_dismissed_path,
    should_show_lan_banner,
    should_show_welcome,
)
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
    pending_rows = (
        db.query(Member)
        .filter(Member.status == MemberStatus.RENEWAL_PENDING.value)
        .order_by(Member.renewal_date)
        .limit(5)
        .all()
    )
    pending_members = [MemberService.to_schema(m) for m in pending_rows]
    overdue_members = (renewals.expired + pending_members)[:5]
    renewal_feed = (renewals.due_today + renewals.next_7_days)[:6]
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "stats": stats.model_dump(),
            "renewals_today": renewals.due_today[:5],
            "renewals_soon": renewals.next_7_days[:5],
            "renewal_feed": renewal_feed,
            "overdue_members": overdue_members,
            "pending_members": pending_members,
            "today": date.today(),
            "show_welcome": should_show_welcome(),
            "show_lan_banner": user.role == UserRole.ADMIN and should_show_lan_banner(),
            "lan_url": get_lan_url(get_server_port(request)),
        },
    )


@router.post("/lan/dismiss")
async def dismiss_lan(
    request: Request,
    user: UserOut = Depends(require_login),
):
    if user.role == UserRole.ADMIN:
        get_lan_dismissed_path().touch()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/welcome/dismiss")
async def dismiss_welcome(
    request: Request,
    user: UserOut = Depends(require_login),
):
    get_welcome_dismissed_path().touch()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
