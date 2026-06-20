import os
import shutil

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.db.models import User


class DuplicateUserError(Exception):
    pass


def get_user_by_phone(db: Session, phone_number: str) -> User | None:
    return db.scalar(select(User).where(User.phone_number == phone_number))


def register_user(
    db: Session,
    *,
    username: str,
    gender: str,
    phone_number: str,
    email: str,
    password: str,
    role: str,
) -> User:
    existing = db.scalar(
        select(User).where((User.phone_number == phone_number) | (User.email == email))
    )
    if existing is not None:
        raise DuplicateUserError("phone_number hoặc email đã được sử dụng")

    user = User(
        username=username,
        gender=gender,
        phone_number=phone_number,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def save_avatar(db: Session, user: User, file: UploadFile) -> User:
    os.makedirs(settings.upload_dir, exist_ok=True)
    extension = os.path.splitext(file.filename or "")[1] or ".jpg"
    filename = f"avatar_{user.id}{extension}"
    destination = os.path.join(settings.upload_dir, filename)
    with open(destination, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    user.avatar = f"/uploads/{filename}"
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, phone_number: str, password: str) -> User | None:
    user = get_user_by_phone(db, phone_number)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
