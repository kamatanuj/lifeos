"""Bills router — full CRUD + summary + payment history"""
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.models import Bill, BillPayment
from app.schemas import BillCreate, BillUpdate, BillResponse, BillPaymentCreate

router = APIRouter(prefix="/api/bills", tags=["bills"])


@router.get("")
def list_bills(status_filter: str = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Bill).filter(Bill.user_id == user.id)
    if status_filter:
        q = q.filter(Bill.status == status_filter)
    bills = q.order_by(Bill.due_date).all()
    return bills


@router.post("", response_model=BillResponse)
def create_bill(payload: BillCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bill = Bill(user_id=user.id, **payload.model_dump())
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


@router.get("/summary")
def bill_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bills = db.query(Bill).filter(Bill.user_id == user.id).all()
    total_due = sum(b.amount for b in bills if b.status in ("pending", "overdue"))
    paid_this_month = sum(b.paid_amount or 0 for b in bills if b.status == "paid" and b.paid_date and b.paid_date.month == date.today().month)
    upcoming = sum(1 for b in bills if b.status == "pending")
    overdue = sum(1 for b in bills if b.status == "overdue")
    return {"total_due": total_due, "paid_this_month": paid_this_month, "upcoming": upcoming, "overdue": overdue}


@router.get("/{bill_id}", response_model=BillResponse)
def get_bill(bill_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bill = db.query(Bill).filter(Bill.id == bill_id, Bill.user_id == user.id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill


@router.put("/{bill_id}", response_model=BillResponse)
def update_bill(bill_id: int, payload: BillUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bill = db.query(Bill).filter(Bill.id == bill_id, Bill.user_id == user.id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(bill, k, v)
    db.commit()
    db.refresh(bill)
    return bill


@router.delete("/{bill_id}")
def delete_bill(bill_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bill = db.query(Bill).filter(Bill.id == bill_id, Bill.user_id == user.id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    db.delete(bill)
    db.commit()
    return {"deleted": True}


@router.post("/{bill_id}/pay")
def pay_bill(bill_id: int, payload: BillPaymentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bill = db.query(Bill).filter(Bill.id == bill_id, Bill.user_id == user.id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    payment = BillPayment(bill_id=bill_id, **payload.model_dump())
    db.add(payment)
    bill.status = "paid"
    bill.paid_date = payload.paid_date
    bill.paid_amount = payload.amount
    db.commit()
    return {"status": "paid", "payment_id": payment.id}


@router.get("/{bill_id}/history")
def bill_history(bill_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bill = db.query(Bill).filter(Bill.id == bill_id, Bill.user_id == user.id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill.payments