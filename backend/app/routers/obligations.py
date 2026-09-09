"""Obligations router — CRUD + mark paid"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.models import Obligation
from app.schemas import ObligationCreate, ObligationResponse

router = APIRouter(prefix="/api/obligations", tags=["obligations"])


@router.get("")
def list_obligations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Obligation).filter(Obligation.user_id == user.id).order_by(Obligation.next_due_date).all()


@router.get("/summary")
def obligation_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obs = db.query(Obligation).filter(Obligation.user_id == user.id, Obligation.is_active == True).all()
    active = len(obs)
    monthly_total = sum(o.amount for o in obs if o.frequency == "monthly")
    overdue = sum(1 for o in obs if o.next_due_date and o.next_due_date < date.today())
    return {"active": active, "monthly_total": monthly_total, "overdue": overdue}


@router.post("", response_model=ObligationResponse)
def create_obligation(payload: ObligationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = Obligation(user_id=user.id, **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{oid}", response_model=ObligationResponse)
def get_obligation(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(Obligation).filter(Obligation.id == oid, Obligation.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Obligation not found")
    return obj


@router.put("/{oid}", response_model=ObligationResponse)
def update_obligation(oid: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(Obligation).filter(Obligation.id == oid, Obligation.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Obligation not found")
    for k, v in payload.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{oid}")
def delete_obligation(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(Obligation).filter(Obligation.id == oid, Obligation.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Obligation not found")
    db.delete(obj)
    db.commit()
    return {"deleted": True}


@router.post("/{oid}/mark-paid")
def mark_paid(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(Obligation).filter(Obligation.id == oid, Obligation.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Obligation not found")
    obj.last_paid_date = date.today()
    # Advance next_due_date based on frequency
    freq_map = {"monthly": 30, "quarterly": 90, "half_yearly": 180, "yearly": 365}
    days = freq_map.get(obj.frequency, 30)
    obj.next_due_date = date.today() + timedelta(days=days)
    db.commit()
    return {"status": "paid", "next_due_date": obj.next_due_date.isoformat()}


@router.get("/{oid}/history")
def obligation_history(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(Obligation).filter(Obligation.id == oid, Obligation.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Obligation not found")
    return obj.payments