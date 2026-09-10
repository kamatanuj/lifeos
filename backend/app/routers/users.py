"""Users router — admin CRUD for user accounts"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import hash_password
from app.models import User
from app.schemas import UserResponse

router = APIRouter(prefix="/api/users", tags=["users"])


def _require_admin(user: User = Depends(get_current_user)) -> User:
    """Admin = the primary account (lowest id). Extend with a role column if needed later."""
    if user.id != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


@router.get("", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), admin: User = Depends(_require_admin)):
    return db.query(User).order_by(User.id).all()


@router.post("", response_model=UserResponse, status_code=201)
def create_user(payload: dict, db: Session = Depends(get_db), admin: User = Depends(_require_admin)):
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    phone = payload.get("phone") or None
    is_active = bool(payload.get("is_active", True))
    if not name or not email or not password:
        raise HTTPException(status_code=422, detail="name, email and password are required")
    if len(password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="A user with this email already exists")
    obj = User(name=name, email=email, phone=phone, hashed_password=hash_password(password), is_active=is_active)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{uid}", response_model=UserResponse)
def get_user(uid: int, db: Session = Depends(get_db), admin: User = Depends(_require_admin)):
    obj = db.query(User).filter(User.id == uid).first()
    if not obj:
        raise HTTPException(status_code=404, detail="User not found")
    return obj


@router.put("/{uid}", response_model=UserResponse)
def update_user(uid: int, payload: dict, db: Session = Depends(get_db), admin: User = Depends(_require_admin)):
    obj = db.query(User).filter(User.id == uid).first()
    if not obj:
        raise HTTPException(status_code=404, detail="User not found")
    if "name" in payload and payload["name"]:
        obj.name = payload["name"].strip()
    if "phone" in payload:
        obj.phone = payload["phone"] or None
    if "email" in payload and payload["email"]:
        email = payload["email"].strip().lower()
        if email != obj.email and db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=409, detail="A user with this email already exists")
        obj.email = email
    if payload.get("password"):
        if len(payload["password"]) < 6:
            raise HTTPException(status_code=422, detail="Password must be at least 6 characters")
        obj.hashed_password = hash_password(payload["password"])
    if "is_active" in payload:
        if uid == admin.id and payload["is_active"] is False:
            raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
        obj.is_active = bool(payload["is_active"])
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{uid}")
def delete_user(uid: int, db: Session = Depends(get_db), admin: User = Depends(_require_admin)):
    if uid == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    obj = db.query(User).filter(User.id == uid).first()
    if not obj:
        raise HTTPException(status_code=404, detail="User not found")
    # Hard delete — all dependent rows cascade (bills, obligations, documents, ...)
    db.delete(obj)
    db.commit()
    return {"deleted": True}

