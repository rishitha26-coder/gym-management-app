"""Database seeding for demo data."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.auth import seed_users
from app.models import Member, PaymentMethod
from app.services.member_service import MemberService


def seed_sample_members(db: Session) -> None:
    """Insert sample members if database is empty."""
    if db.query(Member).count() > 0:
        return

    today = date.today()
    samples = [
        {
            "full_name": "Rahul Sharma",
            "phone": "9876543210",
            "date_of_joining": today - timedelta(days=60),
            "plan_months": 6,
            "fee_paid": 8000.0,
            "payment_date": today - timedelta(days=60),
            "personal_training_amount": 3000.0,
            "notes": "Prefers morning sessions",
            "payment_method": PaymentMethod.UPI.value,
        },
        {
            "full_name": "Priya Patel",
            "phone": "9123456780",
            "date_of_joining": today - timedelta(days=85),
            "plan_months": 3,
            "fee_paid": 4500.0,
            "payment_date": today - timedelta(days=5),
            "personal_training_amount": None,
            "notes": "",
            "payment_method": PaymentMethod.CASH.value,
        },
        {
            "full_name": "Amit Kumar",
            "phone": "9988776655",
            "date_of_joining": today - timedelta(days=400),
            "plan_months": 12,
            "fee_paid": 12000.0,
            "payment_date": today - timedelta(days=400),
            "personal_training_amount": 5000.0,
            "notes": "VIP member",
            "payment_method": PaymentMethod.CARD.value,
        },
        {
            "full_name": "Sneha Reddy",
            "phone": "9000111222",
            "date_of_joining": today - timedelta(days=10),
            "plan_months": 1,
            "fee_paid": 1500.0,
            "payment_date": today - timedelta(days=10),
            "personal_training_amount": None,
            "notes": "New joiner",
            "payment_method": PaymentMethod.BANK_TRANSFER.value,
        },
        {
            "full_name": "Vikram Singh",
            "phone": "9112233445",
            "date_of_joining": today - timedelta(days=95),
            "plan_months": 3,
            "fee_paid": 4500.0,
            "payment_date": today - timedelta(days=95),
            "personal_training_amount": 2000.0,
            "notes": "Renewal follow-up needed",
            "payment_method": PaymentMethod.UPI.value,
        },
    ]

    for data in samples:
        renewal = MemberService.calculate_renewal_date(
            data["date_of_joining"], data["plan_months"]
        )
        status = MemberService.calculate_status(renewal)
        member = Member(
            full_name=data["full_name"],
            phone=data["phone"],
            date_of_joining=data["date_of_joining"],
            plan_months=data["plan_months"],
            fee_paid=data["fee_paid"],
            payment_date=data["payment_date"],
            renewal_date=renewal,
            personal_training_amount=data["personal_training_amount"],
            notes=data["notes"],
            status=status,
            payment_method=data["payment_method"],
        )
        db.add(member)
    db.commit()


def init_db(db: Session) -> None:
    """Seed users and sample members."""
    seed_users(db)
    seed_sample_members(db)
