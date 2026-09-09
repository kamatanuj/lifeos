"""Insurance router — CRUD + summary"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.models import InsurancePolicy
from app.schemas import InsuranceCreate, InsuranceResponse

router = APIRouter(prefix="/api/insurance", tags=["insurance"])


@router.get("")
def list_insurance(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(InsurancePolicy).filter(InsurancePolicy.user_id == user.id).order_by(InsurancePolicy.renewal_date).all()


@router.get("/summary")
def insurance_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    policies = db.query(InsurancePolicy).filter(InsurancePolicy.user_id == user.id, InsurancePolicy.status == "active").all()
    active = len(policies)
    total_premium = sum(p.premium_amount for p in policies)
    renewing_soon = sum(1 for p in policies if p.renewal_date and p.renewal_date <= date.today() + timedelta(days=90))
    return {"active_policies": active, "total_premium_year": total_premium, "renewing_90_days": renewing_soon}


@router.post("", response_model=InsuranceResponse)
def create_insurance(payload: InsuranceCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = InsurancePolicy(user_id=user.id, **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{iid}", response_model=InsuranceResponse)
def get_insurance(iid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(InsurancePolicy).filter(InsurancePolicy.id == iid, InsurancePolicy.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Policy not found")
    return obj


@router.put("/{iid}", response_model=InsuranceResponse)
def update_insurance(iid: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(InsurancePolicy).filter(InsurancePolicy.id == iid, InsurancePolicy.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Policy not found")
    for k, v in payload.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{iid}")
def delete_insurance(iid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(InsurancePolicy).filter(InsurancePolicy.id == iid, InsurancePolicy.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.delete(obj)
    db.commit()
    return {"deleted": True}