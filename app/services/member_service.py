"""Member business logic and status calculations."""

from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.membership import plan_label
from app.models import Member, MemberStatus
from app.paths import get_uploads_dir, uploads_url_prefix
from app.schemas import MemberCreate, MemberOut, MemberUpdate


class MemberService:
    """Handles member CRUD, photo uploads, and status logic."""

    UPLOAD_DIR = get_uploads_dir()

    @staticmethod
    def add_months(start: date, months: int) -> date:
        """Add calendar months to a date (handles month-end edge cases)."""
        month = start.month - 1 + months
        year = start.year + month // 12
        month = month % 12 + 1
        day = min(start.day, monthrange(year, month)[1])
        return date(year, month, day)

    @classmethod
    def calculate_renewal_date(cls, start: date, plan_months: int) -> date:
        """Compute renewal date from membership duration in months."""
        return cls.add_months(start, plan_months)

    @staticmethod
    def calculate_status(renewal_date: date, today: Optional[date] = None) -> str:
        """Determine member status from renewal date."""
        today = today or date.today()
        if renewal_date < today:
            return MemberStatus.EXPIRED.value
        if renewal_date <= today + timedelta(days=7):
            return MemberStatus.RENEWAL_PENDING.value
        return MemberStatus.ACTIVE.value

    @staticmethod
    def pt_display(amount: Optional[float]) -> str:
        if amount is None or amount <= 0:
            return "NA"
        return f"₹{amount:,.2f}"

    @classmethod
    def to_schema(cls, member: Member) -> MemberOut:
        status = cls.calculate_status(member.renewal_date)
        if member.status != status:
            member.status = status
        return MemberOut(
            id=member.id,
            photo_path=member.photo_path,
            full_name=member.full_name,
            phone=member.phone,
            date_of_joining=member.date_of_joining,
            plan_months=member.plan_months,
            membership_plan=plan_label(member.plan_months),
            fee_paid=member.fee_paid,
            payment_date=member.payment_date,
            renewal_date=member.renewal_date,
            personal_training_amount=member.personal_training_amount,
            personal_training_display=cls.pt_display(member.personal_training_amount),
            notes=member.notes,
            status=MemberStatus(status),
            payment_method=member.payment_method,
            balance=member.balance,
            created_at=member.created_at,
            updated_at=member.updated_at,
        )

    @classmethod
    async def save_photo(cls, upload: UploadFile) -> str:
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        ext = Path(upload.filename or "photo.jpg").suffix.lower()
        if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
            raise HTTPException(status_code=400, detail="Invalid image format")
        filename = f"{uuid4().hex}{ext}"
        filepath = cls.UPLOAD_DIR / filename
        content = await upload.read()
        filepath.write_bytes(content)
        return f"{uploads_url_prefix()}/{filename}"

    @classmethod
    def create(
        cls,
        db: Session,
        data: MemberCreate,
        photo_path: Optional[str] = None,
    ) -> MemberOut:
        existing = db.query(Member).filter(Member.phone == data.phone).first()
        if existing:
            raise HTTPException(status_code=400, detail="Phone number already exists")

        months = data.plan_months.months
        renewal = cls.calculate_renewal_date(data.date_of_joining, months)
        status = cls.calculate_status(renewal)

        member = Member(
            photo_path=photo_path,
            full_name=data.full_name,
            phone=data.phone,
            date_of_joining=data.date_of_joining,
            plan_months=months,
            fee_paid=data.fee_paid,
            payment_date=data.payment_date or data.date_of_joining,
            renewal_date=renewal,
            personal_training_amount=data.personal_training_amount,
            notes=data.notes,
            status=status,
            payment_method=data.payment_method.value if data.payment_method else None,
            balance=data.balance,
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return cls.to_schema(member)

    @classmethod
    def update(
        cls,
        db: Session,
        member_id: int,
        data: MemberUpdate,
        photo_path: Optional[str] = None,
    ) -> MemberOut:
        member = db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        if data.phone and data.phone != member.phone:
            existing = db.query(Member).filter(Member.phone == data.phone).first()
            if existing:
                raise HTTPException(status_code=400, detail="Phone number already exists")
            member.phone = data.phone

        if data.full_name is not None:
            member.full_name = data.full_name
        if data.date_of_joining is not None:
            member.date_of_joining = data.date_of_joining
        if data.plan_months is not None:
            member.plan_months = data.plan_months.months
        if data.fee_paid is not None:
            member.fee_paid = data.fee_paid
        if data.payment_date is not None:
            member.payment_date = data.payment_date
        if data.personal_training_amount is not None:
            member.personal_training_amount = data.personal_training_amount or None
        if data.notes is not None:
            member.notes = data.notes
        if data.payment_method is not None:
            member.payment_method = data.payment_method.value
        if data.balance is not None:
            member.balance = data.balance
        if photo_path:
            member.photo_path = photo_path

        start = member.date_of_joining
        member.renewal_date = cls.calculate_renewal_date(start, member.plan_months)
        member.status = cls.calculate_status(member.renewal_date)

        db.commit()
        db.refresh(member)
        return cls.to_schema(member)

    @classmethod
    def get_by_id(cls, db: Session, member_id: int) -> MemberOut:
        member = db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        return cls.to_schema(member)

    @classmethod
    def get_by_phone(cls, db: Session, phone: str) -> Optional[MemberOut]:
        member = db.query(Member).filter(Member.phone == phone.strip()).first()
        if not member:
            return None
        return cls.to_schema(member)

    @classmethod
    def search(cls, db: Session, query: str) -> list[MemberOut]:
        q = query.strip()
        if not q:
            return []
        members = (
            db.query(Member)
            .filter(
                (Member.phone.contains(q)) | (Member.full_name.ilike(f"%{q}%"))
            )
            .order_by(Member.full_name)
            .limit(50)
            .all()
        )
        return [cls.to_schema(m) for m in members]

    @classmethod
    def delete(cls, db: Session, member_id: int) -> None:
        member = db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        db.delete(member)
        db.commit()

    @classmethod
    def refresh_all_statuses(cls, db: Session) -> None:
        members = db.query(Member).all()
        for member in members:
            member.status = cls.calculate_status(member.renewal_date)
        db.commit()
