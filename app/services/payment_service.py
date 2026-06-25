"""Payment update logic."""

from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Member
from app.schemas import MemberOut, PaymentUpdateForm
from app.services.member_service import MemberService


class PaymentService:
    """Handle payment and renewal updates."""

    @classmethod
    def update_payment(
        cls,
        db: Session,
        member_id: int,
        form: PaymentUpdateForm,
    ) -> MemberOut:
        db_member = db.query(Member).filter(Member.id == member_id).first()
        if not db_member:
            raise HTTPException(status_code=404, detail="Member not found")

        db_member.fee_paid = form.fee_paid
        db_member.payment_date = form.payment_date
        db_member.payment_method = form.payment_method.value
        db_member.balance = form.balance
        if form.personal_training_amount is not None:
            db_member.personal_training_amount = (
                form.personal_training_amount or None
            )

        if form.plan_months:
            db_member.plan_months = form.plan_months.months

        if form.extend_renewal:
            base_date = form.payment_date or date.today()
            db_member.renewal_date = MemberService.calculate_renewal_date(
                base_date,
                db_member.plan_months,
            )

        db_member.status = MemberService.calculate_status(db_member.renewal_date)
        db.commit()
        db.refresh(db_member)
        return MemberService.to_schema(db_member)
