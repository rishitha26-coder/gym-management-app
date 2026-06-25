"""Authentication utilities and session management."""

from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.schemas import UserOut

DEFAULT_USERS = [
    {"username": "admin", "password": "admin123", "role": UserRole.ADMIN.value},
    {"username": "staff", "password": "staff123", "role": UserRole.STAFF.value},
]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def seed_users(db: Session) -> None:
    """Create default admin and staff users if none exist."""
    if db.query(User).count() > 0:
        return
    for user_data in DEFAULT_USERS:
        user = User(
            username=user_data["username"],
            password_hash=hash_password(user_data["password"]),
            role=user_data["role"],
        )
        db.add(user)
    db.commit()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def require_login(request: Request, db: Session = Depends(get_db)) -> UserOut:
    user = get_current_user(request, db)
    return UserOut.model_validate(user)


def require_admin(user: UserOut = Depends(require_login)) -> UserOut:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def can_edit_member(user: UserOut) -> bool:
    return user.role == UserRole.ADMIN


def can_delete_member(user: UserOut) -> bool:
    return user.role == UserRole.ADMIN
