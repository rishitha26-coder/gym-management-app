"""Pydantic schemas for request/response validation."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.membership import PlanMonths
from app.models import MemberStatus, PaymentMethod, UserRole


class UserOut(BaseModel):
    id: int
    username: str
    role: UserRole

    model_config = {"from_attributes": True}

    @property
    def role_label(self) -> str:
        return "Admin" if self.role == UserRole.ADMIN else "Staff"


class LoginForm(BaseModel):
    username: str
    password: str


class DashboardStats(BaseModel):
    total_members: int
    active_members: int
    renewal_pending: int
    expired_members: int
    renewals_today: int
    renewals_next_7_days: int
    total_collected: float
    personal_training_collected: float
    fee_this_month: float
    pt_this_month: float


class MemberBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=5, max_length=20)
    date_of_joining: date
    plan_months: PlanMonths
    fee_paid: float = Field(ge=0)
    payment_date: Optional[date] = None
    personal_training_amount: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    balance: Optional[float] = Field(default=None, ge=0)

    @field_validator("phone")
    @classmethod
    def strip_phone(cls, value: str) -> str:
        return value.strip()


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    phone: Optional[str] = Field(default=None, min_length=5, max_length=20)
    date_of_joining: Optional[date] = None
    plan_months: Optional[PlanMonths] = None
    fee_paid: Optional[float] = Field(default=None, ge=0)
    payment_date: Optional[date] = None
    personal_training_amount: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    balance: Optional[float] = Field(default=None, ge=0)


class MemberOut(BaseModel):
    id: int
    photo_path: Optional[str] = None
    full_name: str
    phone: str
    date_of_joining: date
    plan_months: int
    membership_plan: str
    fee_paid: float
    payment_date: Optional[date] = None
    renewal_date: date
    personal_training_amount: Optional[float] = None
    personal_training_display: str
    notes: Optional[str] = None
    status: MemberStatus
    payment_method: Optional[str] = None
    balance: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentUpdateForm(BaseModel):
    fee_paid: float = Field(ge=0)
    payment_date: date
    payment_method: PaymentMethod
    balance: Optional[float] = Field(default=None, ge=0)
    personal_training_amount: Optional[float] = Field(default=None, ge=0)
    plan_months: Optional[PlanMonths] = None
    extend_renewal: bool = False


class SearchResult(BaseModel):
    members: list[MemberOut]
    query: str


class RenewalListOut(BaseModel):
    due_today: list[MemberOut]
    next_7_days: list[MemberOut]
    expired: list[MemberOut]
    active: list[MemberOut]


class ReportExportOption(BaseModel):
    """Single export action shown on the Reports page."""

    title: str
    description: str
    xlsx_url: str
    csv_url: str


class ReportsPageOut(BaseModel):
    """Grouped export options for the Reports page."""

    member_reports: list[ReportExportOption]
    financial_reports: list[ReportExportOption]
    summary_pdf_url: str
