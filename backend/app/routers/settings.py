"""Settings router"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.models import User

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings(user: User = Depends(get_current_user)):
    return {
        "profile": {"name": user.name, "email": user.email, "phone": user.phone},
        "security": {"is_2fa_enabled": user.is_2fa_enabled, "is_active": user.is_active},
        "preferences": {"reminder_frequency": "daily", "email_notifications": True, "overdue_alerts": True},
    }


@router.put("/profile")
def update_profile(payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    for k in ("name", "phone"):
        if k in payload:
            setattr(user, k, payload[k])
    db.commit()
    return {"updated": True}


@router.put("/password")
def change_password(payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    old = payload.get("old_password", "")
    new = payload.get("new_password", "")
    if not verify_password(old, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password incorrect")
    user.hashed_password = hash_password(new)
    db.commit()
    return {"changed": True}