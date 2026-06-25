"""Report export routes."""

from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import require_login
from app.database import get_db
from app.paths import get_templates_dir
from app.schemas import ReportExportOption, ReportsPageOut, UserOut
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])
templates = Jinja2Templates(directory=str(get_templates_dir()))


def _reports_page_data() -> ReportsPageOut:
    return ReportsPageOut(
        member_reports=[
            ReportExportOption(
                title="All Members",
                description="Complete member directory with plan, fees, and status.",
                xlsx_url="/reports/all-members.xlsx",
                csv_url="/reports/all-members.csv",
            ),
            ReportExportOption(
                title="Renewal Pending",
                description="Members due for renewal within the next 7 days.",
                xlsx_url="/reports/renewal-pending.xlsx",
                csv_url="/reports/renewal-pending.csv",
            ),
            ReportExportOption(
                title="Expired Members",
                description="Members whose membership has expired.",
                xlsx_url="/reports/expired.xlsx",
                csv_url="/reports/expired.csv",
            ),
        ],
        financial_reports=[
            ReportExportOption(
                title="Monthly Fee Collection",
                description="Membership fees collected in the current month.",
                xlsx_url="/reports/monthly-fees.xlsx",
                csv_url="/reports/monthly-fees.csv",
            ),
            ReportExportOption(
                title="Personal Training Collection",
                description="Personal training payments recorded for all members.",
                xlsx_url="/reports/personal-training.xlsx",
                csv_url="/reports/personal-training.csv",
            ),
        ],
        summary_pdf_url="/reports/summary.pdf",
    )


def _csv_response(content: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _xlsx_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("")
async def reports_page(
    request: Request,
    user: UserOut = Depends(require_login),
):
    reports = _reports_page_data()
    return templates.TemplateResponse(
        request,
        "reports.html",
        {"user": user, "reports": reports},
    )


@router.get("/all-members.csv")
async def export_all_csv(
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    content = ReportService.export_all_members_csv(db)
    return _csv_response(content, "gym_all_members.csv")


@router.get("/all-members.xlsx")
async def export_all_xlsx(
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    content = ReportService.export_all_members_xlsx(db)
    return _xlsx_response(content, "gym_all_members.xlsx")


@router.get("/renewal-pending.csv")
async def export_pending_csv(
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    content = ReportService.export_renewal_pending_csv(db)
    return _csv_response(content, "gym_renewal_pending.csv")


@router.get("/renewal-pending.xlsx")
async def export_pending_xlsx(
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    content = ReportService.export_renewal_pending_xlsx(db)
    return _xlsx_response(content, "gym_renewal_pending.xlsx")


@router.get("/expired.csv")
async def export_expired_csv(
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    content = ReportService.export_expired_csv(db)
    return _csv_response(content, "gym_expired_members.csv")


@router.get("/expired.xlsx")
async def export_expired_xlsx(
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    content = ReportService.export_expired_xlsx(db)
    return _xlsx_response(content, "gym_expired_members.xlsx")


@router.get("/monthly-fees.csv")
async def export_monthly_csv(
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    content = ReportService.export_monthly_fees_csv(db)
    today = date.today()
    filename = f"gym_monthly_fees_{today.year}_{today.month:02d}.csv"
    return _csv_response(content, filename)


@router.get("/monthly-fees.xlsx")
async def export_monthly_xlsx(
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    content = ReportService.export_monthly_fees_xlsx(db)
    today = date.today()
    filename = f"gym_monthly_fees_{today.year}_{today.month:02d}.xlsx"
    return _xlsx_response(content, filename)


@router.get("/personal-training.csv")
async def export_pt_csv(
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    content = ReportService.export_personal_training_csv(db)
    return _csv_response(content, "gym_personal_training.csv")


@router.get("/personal-training.xlsx")
async def export_pt_xlsx(
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    content = ReportService.export_personal_training_xlsx(db)
    return _xlsx_response(content, "gym_personal_training.xlsx")


@router.get("/summary.pdf")
async def export_pdf(
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    content = ReportService.export_summary_pdf(db)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="gym_summary_report.pdf"'},
    )
