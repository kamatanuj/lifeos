"""Obligations router — CRUD + mark paid"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.models import Obligation, ObligationPayment
from app.schemas import ObligationCreate, ObligationResponse

router = APIRouter(prefix="/api/obligations", tags=["obligations"])


@router.get("")
def list_obligations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obs = db.query(Obligation).filter(Obligation.user_id == user.id).order_by(Obligation.next_due_date).all()
    _carry_forward_unpaid(db, user.id, obs)
    return obs


@router.get("/summary")
def obligation_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obs = db.query(Obligation).filter(Obligation.user_id == user.id, Obligation.is_active == True).all()
    _carry_forward_unpaid(db, user.id, obs)
    today = date.today()
    active = len([o for o in obs if o.next_due_date >= today])
    # "Monthly Total" = amounts falling due in THIS CALENDAR MONTH
    monthly_total = sum(o.amount for o in obs if o.next_due_date and o.next_due_date.month == today.month and o.next_due_date.year == today.year)
    overdue = sum(1 for o in obs if o.next_due_date and o.next_due_date < today)
    return {"active": active, "monthly_total": monthly_total, "overdue": overdue}


def _carry_forward_unpaid(db: Session, user_id: int, obs) -> None:
    """When an obligation's due date has passed unpaid, keep the overdue entry AND
    create the next-cycle entry (idempotent) so the user sees last month as pending."""
    freq_map = {"monthly": 30, "quarterly": 90, "half_yearly": 180, "yearly": 365}
    from datetime import timedelta
    existing_dues = {(o.name, o.next_due_date) for o in obs}
    for o in list(obs):
        if not (o.next_due_date and o.next_due_date < date.today()):
            continue  # not overdue
        # only carry forward monthly obligations (the cycle user asked about)
        if (o.frequency or "monthly") != "monthly":
            continue
        if o.last_paid_date and o.last_paid_date >= o.next_due_date:
            continue  # already paid for that cycle
        next_due = o.next_due_date + timedelta(days=freq_map.get(o.frequency, 30))
        if (o.name, next_due) in existing_dues:
            continue  # already carried
        clone = Obligation(
            user_id=user_id,
            name=o.name,
            category=o.category,
            amount=o.amount,
            frequency=o.frequency,
            next_due_date=next_due,
            linked_property_id=o.linked_property_id,
            reminder_days_before=o.reminder_days_before,
            payment_method=o.payment_method,
            repeat_until_completed=o.repeat_until_completed,
            send_to_family=o.send_to_family,
            is_active=True,
        )
        db.add(clone)
        existing_dues.add((o.name, next_due))
    db.commit()
    obs[:] = db.query(Obligation).filter(Obligation.user_id == user_id, Obligation.is_active == True).all()


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
    prev_due = obj.next_due_date
    obj.next_due_date = date.today() + timedelta(days=days)
    # Record the payment so history is real
    pay = ObligationPayment(obligation_id=obj.id, amount=obj.amount, paid_date=date.today(), method=obj.payment_method)
    db.add(pay)
    db.commit()
    return {"status": "paid", "next_due_date": obj.next_due_date.isoformat(), "previous_due_date": prev_due.isoformat()}


@router.post("/{oid}/mark-unpaid")
def mark_unpaid(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Undo the latest mark-paid: clear last_paid_date and step the due date back one cycle."""
    obj = db.query(Obligation).filter(Obligation.id == oid, Obligation.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Obligation not found")
    if not obj.last_paid_date:
        raise HTTPException(status_code=400, detail="Obligation is not marked paid")
    freq_map = {"monthly": 30, "quarterly": 90, "half_yearly": 180, "yearly": 365}
    days = freq_map.get(obj.frequency, 30)
    obj.next_due_date = max(obj.next_due_date - timedelta(days=days), date.today() - timedelta(days=365))
    obj.last_paid_date = None
    # Remove the most recent payment row created by the undo pair
    last_pay = db.query(ObligationPayment).filter(ObligationPayment.obligation_id == obj.id).order_by(ObligationPayment.paid_date.desc(), ObligationPayment.id.desc()).first()
    if last_pay:
        db.delete(last_pay)
    db.commit()
    return {"status": "unpaid", "next_due_date": obj.next_due_date.isoformat()}


@router.get("/{oid}/history")
def obligation_history(oid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(Obligation).filter(Obligation.id == oid, Obligation.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Obligation not found")
    return obj.payments