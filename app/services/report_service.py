"""CSV, Excel, and PDF report generation."""

import csv
import io
from datetime import date
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.membership import plan_label
from app.models import Member, MemberStatus
from app.services.member_service import MemberService


class ReportService:
    """Export member and payment reports."""

    MEMBER_HEADERS = [
        "Member ID",
        "Full Name",
        "Phone",
        "Date of Joining",
        "Plan (Months)",
        "Plan Label",
        "Fee Paid (INR)",
        "Payment Date",
        "Renewal Date",
        "Personal Training (INR)",
        "Membership Status",
        "Payment Method",
        "Balance (INR)",
        "Notes",
    ]

    @classmethod
    def _member_rows(cls, members: list[Member]) -> list[list]:
        rows = []
        for member in members:
            rows.append([
                member.id,
                member.full_name,
                member.phone,
                member.date_of_joining.isoformat(),
                member.plan_months,
                plan_label(member.plan_months),
                round(member.fee_paid, 2),
                member.payment_date.isoformat() if member.payment_date else "",
                member.renewal_date.isoformat(),
                member.personal_training_amount or 0,
                MemberService.calculate_status(member.renewal_date),
                member.payment_method or "",
                member.balance if member.balance is not None else "",
                (member.notes or "").replace("\n", " "),
            ])
        return rows

    @classmethod
    def _monthly_fee_rows(
        cls,
        db: Session,
        month: Optional[int] = None,
        year: Optional[int] = None,
    ) -> tuple[list[list], float]:
        today = date.today()
        month = month or today.month
        year = year or today.year
        members = db.query(Member).filter(Member.payment_date.isnot(None)).all()
        filtered = [
            member for member in members
            if member.payment_date
            and member.payment_date.month == month
            and member.payment_date.year == year
        ]
        rows = []
        total = 0.0
        for member in filtered:
            rows.append([
                member.full_name,
                member.phone,
                round(member.fee_paid, 2),
                member.payment_date.isoformat(),
                member.payment_method or "",
                member.plan_months,
                plan_label(member.plan_months),
            ])
            total += member.fee_paid
        return rows, total

    @classmethod
    def _pt_rows(cls, db: Session) -> tuple[list[list], float]:
        members = (
            db.query(Member)
            .filter(Member.personal_training_amount.isnot(None))
            .filter(Member.personal_training_amount > 0)
            .order_by(Member.full_name)
            .all()
        )
        rows = []
        total = 0.0
        for member in members:
            amount = member.personal_training_amount or 0
            rows.append([
                member.full_name,
                member.phone,
                round(amount, 2),
                member.payment_date.isoformat() if member.payment_date else "",
            ])
            total += amount
        return rows, total

    @classmethod
    def _to_csv(cls, headers: list[str], rows: list[list]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        return output.getvalue()

    @classmethod
    def _to_xlsx(
        cls,
        sheet_title: str,
        headers: list[str],
        rows: list[list],
        footer_rows: Optional[list[list]] = None,
    ) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = sheet_title[:31]
        sheet.append(headers)
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        for row in rows:
            sheet.append(row)
        if footer_rows:
            sheet.append([])
            for footer in footer_rows:
                sheet.append(footer)
        buffer = io.BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    @classmethod
    def _filtered_members(cls, db: Session, status: MemberStatus) -> list[Member]:
        members = db.query(Member).order_by(Member.renewal_date).all()
        return [
            member for member in members
            if MemberService.calculate_status(member.renewal_date) == status.value
        ]

    @classmethod
    def export_all_members_csv(cls, db: Session) -> str:
        members = db.query(Member).order_by(Member.full_name).all()
        return cls._to_csv(cls.MEMBER_HEADERS, cls._member_rows(members))

    @classmethod
    def export_all_members_xlsx(cls, db: Session) -> bytes:
        members = db.query(Member).order_by(Member.full_name).all()
        return cls._to_xlsx(
            "All Members",
            cls.MEMBER_HEADERS,
            cls._member_rows(members),
        )

    @classmethod
    def export_renewal_pending_csv(cls, db: Session) -> str:
        pending = cls._filtered_members(db, MemberStatus.RENEWAL_PENDING)
        return cls._to_csv(cls.MEMBER_HEADERS, cls._member_rows(pending))

    @classmethod
    def export_renewal_pending_xlsx(cls, db: Session) -> bytes:
        pending = cls._filtered_members(db, MemberStatus.RENEWAL_PENDING)
        return cls._to_xlsx(
            "Renewal Pending",
            cls.MEMBER_HEADERS,
            cls._member_rows(pending),
        )

    @classmethod
    def export_expired_csv(cls, db: Session) -> str:
        expired = cls._filtered_members(db, MemberStatus.EXPIRED)
        expired.sort(key=lambda member: member.renewal_date, reverse=True)
        return cls._to_csv(cls.MEMBER_HEADERS, cls._member_rows(expired))

    @classmethod
    def export_expired_xlsx(cls, db: Session) -> bytes:
        expired = cls._filtered_members(db, MemberStatus.EXPIRED)
        expired.sort(key=lambda member: member.renewal_date, reverse=True)
        return cls._to_xlsx(
            "Expired Members",
            cls.MEMBER_HEADERS,
            cls._member_rows(expired),
        )

    @classmethod
    def export_monthly_fees_csv(
        cls,
        db: Session,
        month: Optional[int] = None,
        year: Optional[int] = None,
    ) -> str:
        today = date.today()
        month = month or today.month
        year = year or today.year
        headers = [
            "Member Name",
            "Phone",
            "Fee Paid (INR)",
            "Payment Date",
            "Payment Method",
            "Plan (Months)",
            "Plan Label",
        ]
        rows, total = cls._monthly_fee_rows(db, month, year)
        output = cls._to_csv(headers, rows)
        output += f"\nTotal Collected (INR),,,{total:.2f},,\n"
        return output

    @classmethod
    def export_monthly_fees_xlsx(
        cls,
        db: Session,
        month: Optional[int] = None,
        year: Optional[int] = None,
    ) -> bytes:
        today = date.today()
        month = month or today.month
        year = year or today.year
        headers = [
            "Member Name",
            "Phone",
            "Fee Paid (INR)",
            "Payment Date",
            "Payment Method",
            "Plan (Months)",
            "Plan Label",
        ]
        rows, total = cls._monthly_fee_rows(db, month, year)
        return cls._to_xlsx(
            f"Fees {year}-{month:02d}",
            headers,
            rows,
            footer_rows=[["Total Collected (INR)", "", round(total, 2)]],
        )

    @classmethod
    def export_personal_training_csv(cls, db: Session) -> str:
        headers = [
            "Member Name",
            "Phone",
            "Personal Training Amount (INR)",
            "Payment Date",
        ]
        rows, total = cls._pt_rows(db)
        output = cls._to_csv(headers, rows)
        output += f"\nTotal PT Collected (INR),,{total:.2f},\n"
        return output

    @classmethod
    def export_personal_training_xlsx(cls, db: Session) -> bytes:
        headers = [
            "Member Name",
            "Phone",
            "Personal Training Amount (INR)",
            "Payment Date",
        ]
        rows, total = cls._pt_rows(db)
        return cls._to_xlsx(
            "Personal Training",
            headers,
            rows,
            footer_rows=[["Total PT Collected (INR)", "", round(total, 2)]],
        )

    @classmethod
    def export_summary_pdf(cls, db: Session) -> bytes:
        """Generate a simple PDF summary report."""
        members = db.query(Member).all()
        active = sum(
            1 for member in members
            if MemberService.calculate_status(member.renewal_date)
            == MemberStatus.ACTIVE.value
        )
        pending = sum(
            1 for member in members
            if MemberService.calculate_status(member.renewal_date)
            == MemberStatus.RENEWAL_PENDING.value
        )
        expired = sum(
            1 for member in members
            if MemberService.calculate_status(member.renewal_date)
            == MemberStatus.EXPIRED.value
        )
        total_fees = sum(member.fee_paid for member in members)
        total_pt = sum(member.personal_training_amount or 0 for member in members)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = [
            Paragraph("Celebrity Fitness Studio — Summary Report", styles["Title"]),
            Spacer(1, 12),
            Paragraph(f"Generated: {date.today().isoformat()}", styles["Normal"]),
            Spacer(1, 24),
        ]

        data = [
            ["Metric", "Count/Amount"],
            ["Total Members", str(len(members))],
            ["Active", str(active)],
            ["Renewal Pending", str(pending)],
            ["Expired", str(expired)],
            ["Total Fees Collected", f"₹{total_fees:,.2f}"],
            ["Total PT Collected", f"₹{total_pt:,.2f}"],
        ]
        table = Table(data, colWidths=[250, 200])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f4f8")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        doc.build(elements)
        return buffer.getvalue()
