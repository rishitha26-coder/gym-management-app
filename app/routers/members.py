"""Member CRUD, search, and renewal routes."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import can_delete_member, can_edit_member, require_admin, require_login
from app.database import get_db
from app.membership import PlanMonths, plan_choices
from app.models import PaymentMethod
from app.paths import get_templates_dir
from app.schemas import MemberCreate, MemberUpdate, PaymentUpdateForm, UserOut
from app.services.member_service import MemberService
from app.services.payment_service import PaymentService
from app.services.renewal_service import RenewalService

router = APIRouter(tags=["members"])
templates = Jinja2Templates(directory=str(get_templates_dir()))


def _plans():
    return plan_choices()


def _payment_methods():
    return [p.value for p in PaymentMethod]


@router.get("/members/add")
async def add_member_form(
    request: Request,
    user: UserOut = Depends(require_login),
):
    return templates.TemplateResponse(
        request,
        "member_form.html",
        {
            "user": user,
            "member": None,
            "plans": _plans(),
            "payment_methods": _payment_methods(),
            "action": "/members/add",
            "title": "Add Member",
        },
    )


@router.post("/members/add")
async def add_member_submit(
    request: Request,
    full_name: str = Form(...),
    phone: str = Form(...),
    date_of_joining: date = Form(...),
    plan_months: int = Form(...),
    fee_paid: float = Form(...),
    payment_date: Optional[date] = Form(None),
    personal_training_amount: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
    payment_method: Optional[str] = Form(None),
    balance: Optional[float] = Form(None),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    photo_path = None
    if photo and photo.filename:
        photo_path = await MemberService.save_photo(photo)

    try:
        data = MemberCreate(
            full_name=full_name,
            phone=phone,
            date_of_joining=date_of_joining,
            plan_months=PlanMonths(months=plan_months),
            fee_paid=fee_paid,
            payment_date=payment_date,
            personal_training_amount=personal_training_amount,
            notes=notes,
            payment_method=PaymentMethod(payment_method) if payment_method else None,
            balance=balance,
        )
        member = MemberService.create(db, data, photo_path)
    except (HTTPException, ValueError) as exc:
        detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
        return templates.TemplateResponse(
            request,
            "member_form.html",
            {
                "user": user,
                "member": None,
                "plans": _plans(),
                "payment_methods": _payment_methods(),
                "action": "/members/add",
                "title": "Add Member",
                "error": detail,
            },
            status_code=400,
        )
    return RedirectResponse(
        url=f"/members/{member.id}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/members/{member_id}")
async def member_profile(
    request: Request,
    member_id: int,
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    member = MemberService.get_by_id(db, member_id)
    return templates.TemplateResponse(
        request,
        "member_profile.html",
        {
            "user": user,
            "member": member,
            "can_edit": can_edit_member(user),
            "can_delete": can_delete_member(user),
        },
    )


@router.get("/members/{member_id}/edit")
async def edit_member_form(
    request: Request,
    member_id: int,
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_admin),
):
    member = MemberService.get_by_id(db, member_id)
    return templates.TemplateResponse(
        request,
        "member_form.html",
        {
            "user": user,
            "member": member,
            "plans": _plans(),
            "payment_methods": _payment_methods(),
            "action": f"/members/{member_id}/edit",
            "title": "Edit Member",
        },
    )


@router.post("/members/{member_id}/edit")
async def edit_member_submit(
    request: Request,
    member_id: int,
    full_name: str = Form(...),
    phone: str = Form(...),
    date_of_joining: date = Form(...),
    plan_months: int = Form(...),
    fee_paid: float = Form(...),
    payment_date: Optional[date] = Form(None),
    personal_training_amount: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
    payment_method: Optional[str] = Form(None),
    balance: Optional[float] = Form(None),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_admin),
):
    photo_path = None
    if photo and photo.filename:
        photo_path = await MemberService.save_photo(photo)

    try:
        data = MemberUpdate(
            full_name=full_name,
            phone=phone,
            date_of_joining=date_of_joining,
            plan_months=PlanMonths(months=plan_months),
            fee_paid=fee_paid,
            payment_date=payment_date,
            personal_training_amount=personal_training_amount,
            notes=notes,
            payment_method=PaymentMethod(payment_method) if payment_method else None,
            balance=balance,
        )
        member = MemberService.update(db, member_id, data, photo_path)
    except (HTTPException, ValueError) as exc:
        detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
        member = MemberService.get_by_id(db, member_id)
        return templates.TemplateResponse(
            request,
            "member_form.html",
            {
                "user": user,
                "member": member,
                "plans": _plans(),
                "payment_methods": _payment_methods(),
                "action": f"/members/{member_id}/edit",
                "title": "Edit Member",
                "error": detail,
            },
            status_code=400,
        )
    return RedirectResponse(
        url=f"/members/{member.id}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/members/{member_id}/delete")
async def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_admin),
):
    MemberService.delete(db, member_id)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/search")
async def search_page(
    request: Request,
    q: str = "",
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    members = MemberService.search(db, q) if q else []
    phone_match = MemberService.get_by_phone(db, q) if q else None
    if phone_match and phone_match not in members:
        members = [phone_match] + members
    return templates.TemplateResponse(
        request,
        "search.html",
        {"user": user, "query": q, "members": members},
    )


@router.get("/renewals")
async def renewals_page(
    request: Request,
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    renewals = RenewalService.get_renewal_lists(db)
    return templates.TemplateResponse(
        request,
        "renewals.html",
        {"user": user, "renewals": renewals},
    )


@router.get("/members/{member_id}/payment")
async def payment_form(
    request: Request,
    member_id: int,
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    member = MemberService.get_by_id(db, member_id)
    return templates.TemplateResponse(
        request,
        "payment_form.html",
        {
            "user": user,
            "member": member,
            "plans": _plans(),
            "payment_methods": _payment_methods(),
        },
    )


@router.post("/members/{member_id}/payment")
async def payment_submit(
    request: Request,
    member_id: int,
    fee_paid: float = Form(...),
    payment_date: date = Form(...),
    payment_method: str = Form(...),
    balance: Optional[float] = Form(None),
    personal_training_amount: Optional[float] = Form(None),
    plan_months: Optional[int] = Form(None),
    extend_renewal: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: UserOut = Depends(require_login),
):
    try:
        form = PaymentUpdateForm(
            fee_paid=fee_paid,
            payment_date=payment_date,
            payment_method=PaymentMethod(payment_method),
            balance=balance,
            personal_training_amount=personal_training_amount,
            plan_months=PlanMonths(months=plan_months) if plan_months else None,
            extend_renewal=extend_renewal == "on",
        )
        member = PaymentService.update_payment(db, member_id, form)
    except (HTTPException, ValueError) as exc:
        detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
        member = MemberService.get_by_id(db, member_id)
        return templates.TemplateResponse(
            request,
            "payment_form.html",
            {
                "user": user,
                "member": member,
                "plans": _plans(),
                "payment_methods": _payment_methods(),
                "error": detail,
            },
            status_code=400,
        )
    return RedirectResponse(
        url=f"/members/{member.id}", status_code=status.HTTP_303_SEE_OTHER
    )
