"""Health router — profiles + records + summary"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.models import HealthProfile, HealthRecord, HealthDocument
from app.schemas import HealthProfileCreate, HealthProfileResponse, HealthRecordCreate, HealthRecordResponse

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/profiles")
def list_profiles(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(HealthProfile).filter(HealthProfile.user_id == user.id).all()


@router.post("/profiles", response_model=HealthProfileResponse)
def create_profile(payload: HealthProfileCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = HealthProfile(user_id=user.id, **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/profiles/{pid}", response_model=HealthProfileResponse)
def get_profile(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(HealthProfile).filter(HealthProfile.id == pid, HealthProfile.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    return obj


@router.put("/profiles/{pid}", response_model=HealthProfileResponse)
def update_profile(pid: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(HealthProfile).filter(HealthProfile.id == pid, HealthProfile.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    for k, v in payload.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/profiles/{pid}")
def delete_profile(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(HealthProfile).filter(HealthProfile.id == pid, HealthProfile.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(obj)
    db.commit()
    return {"deleted": True}


@router.get("/profiles/{pid}/records")
def list_records(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = db.query(HealthProfile).filter(HealthProfile.id == pid, HealthProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile.records


@router.post("/profiles/{pid}/records", response_model=HealthRecordResponse)
def create_record(pid: int, payload: HealthRecordCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = db.query(HealthProfile).filter(HealthProfile.id == pid, HealthProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    obj = HealthRecord(profile_id=pid, **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/summary")
def health_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profiles = db.query(HealthProfile).filter(HealthProfile.user_id == user.id).all()
    active_medications = 0
    upcoming_appointments = 0
    for p in profiles:
        for r in p.records:
            if r.medications:
                active_medications += 1
            if r.next_appointment:
                upcoming_appointments += 1
    return {"profiles": len(profiles), "active_medications": active_medications, "upcoming_appointments": upcoming_appointments}