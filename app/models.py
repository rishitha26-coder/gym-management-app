"""SQLAlchemy ORM models."""

from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"


class MemberStatus(str, Enum):
    ACTIVE = "Active"
    RENEWAL_PENDING = "Renewal Pending"
    EXPIRED = "Expired"


class PaymentMethod(str, Enum):
    CASH = "Cash"
    UPI = "UPI"
    CARD = "Card"
    BANK_TRANSFER = "Bank Transfer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.STAFF.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    photo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    date_of_joining: Mapped[date] = mapped_column(Date)
    plan_months: Mapped[int] = mapped_column(Integer, default=3)
    fee_paid: Mapped[float] = mapped_column(Float, default=0.0)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    renewal_date: Mapped[date] = mapped_column(Date, index=True)
    personal_training_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=MemberStatus.ACTIVE.value)
    payment_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    balance: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
