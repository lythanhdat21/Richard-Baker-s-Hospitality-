from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.core.timeutil import to_vn_str
from app.db.session import get_db
from app.schemas.user import Gender, LoginRequest, Role
from app.services.user_service import (
    DuplicateUserError,
    authenticate_user,
    register_user,
    save_avatar,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_endpoint(
    username: str = Form(...),
    gender: Gender = Form(...),
    phone_number: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: Role = Form(...),
    avatar: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        user = register_user(
            db,
            username=username,
            gender=gender.value,
            phone_number=phone_number,
            email=email,
            password=password,
            role=role.value,
        )
    except DuplicateUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(exc), "status": "error"},
        )

    user = save_avatar(db, user, avatar)

    return {
        "message": "Register success",
        "status": "success",
        "data": {
            "id": user.id,
            "username": user.username,
            "phone_number": user.phone_number,
            "email": user.email,
            "role": user.role,
            "avatar": user.avatar,
            "created_at": to_vn_str(user.created_at),
        },
    }


@router.post("/login")
def login_endpoint(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.phone_number, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Số điện thoại hoặc mật khẩu không đúng", "status": "error"},
        )

    token = create_access_token(user.id, user.role)

    return {
        "message": "Login success",
        "status": "success",
        "data": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "avatar": user.avatar,
            "created_at": to_vn_str(user.created_at),
            "access_token": token,
        },
    }
