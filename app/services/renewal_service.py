"""Renewal tracking and dashboard statistics."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import Member, MemberStatus
from app.schemas import DashboardStats, RenewalListOut
from app.services.member_service import MemberService


class RenewalService:
    """Renewal lists and dashboard metrics."""

    @staticmethod
    def _today() -> date:
        return date.today()

    @classmethod
    def get_renewal_lists(cls, db: Session) -> RenewalListOut:
        today = cls._today()
        week_end = today + timedelta(days=7)
        members = db.query(Member).order_by(Member.renewal_date).all()
        schemas = [MemberService.to_schema(m) for m in members]

        due_today = [m for m in schemas if m.renewal_date == today]
        next_7 = [
            m for m in schemas
            if today < m.renewal_date <= week_end
        ]
        expired = [m for m in schemas if m.status == MemberStatus.EXPIRED]
        active = [m for m in schemas if m.status == MemberStatus.ACTIVE]

        return RenewalListOut(
            due_today=due_today,
            next_7_days=next_7,
            expired=expired,
            active=active,
        )

    @classmethod
    def get_dashboard_stats(cls, db: Session) -> DashboardStats:
        today = cls._today()
        week_end = today + timedelta(days=7)
        members = db.query(Member).all()

        MemberService.refresh_all_statuses(db)
        members = db.query(Member).all()

        total = len(members)
        active = sum(1 for m in members if m.status == MemberStatus.ACTIVE.value)
        pending = sum(1 for m in members if m.status == MemberStatus.RENEWAL_PENDING.value)
        expired = sum(1 for m in members if m.status == MemberStatus.EXPIRED.value)
        today_count = sum(1 for m in members if m.renewal_date == today)
        week_count = sum(
            1 for m in members if today < m.renewal_date <= week_end
        )
        total_collected = sum(m.fee_paid for m in members)
        pt_collected = sum(
            m.personal_training_amount or 0 for m in members
        )

        return DashboardStats(
            total_members=total,
            active_members=active,
            renewal_pending=pending,
            expired_members=expired,
            renewals_today=today_count,
            renewals_next_7_days=week_count,
            total_collected=total_collected,
            personal_training_collected=pt_collected,
        )
