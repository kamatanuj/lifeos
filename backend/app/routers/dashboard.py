"""Dashboard router — aggregated summary"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.models import Bill, Obligation, InsurancePolicy, Property, MaintenanceRecord, HealthProfile, HealthRecord

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = date.today()
    week_later = today + timedelta(days=7)

    # Counts
    bills = db.query(Bill).filter(Bill.user_id == user.id).all()
    obligations = db.query(Obligation).filter(Obligation.user_id == user.id, Obligation.is_active == True).all()
    properties = db.query(Property).filter(Property.user_id == user.id).all()
    health_profiles = db.query(HealthProfile).filter(HealthProfile.user_id == user.id).all()

    due_this_week = sum(1 for b in bills if b.status == "pending" and b.due_date and today <= b.due_date <= week_later)
    total_bills_month = sum(b.amount for b in bills if b.due_date and b.due_date.month == today.month)
    health_reminders = sum(1 for p in health_profiles for r in p.records if r.next_appointment and today <= r.next_appointment <= week_later)

    # Upcoming due dates (next 5)
    upcoming = []
    for b in bills:
        if b.status == "pending" and b.due_date:
            upcoming.append({"type": "bill", "title": f"{b.bill_type} - {b.provider}", "date": b.due_date.isoformat(), "amount": b.amount, "overdue": b.due_date < today})
    for o in obligations:
        if o.next_due_date:
            upcoming.append({"type": "obligation", "title": o.name, "date": o.next_due_date.isoformat(), "amount": o.amount, "overdue": o.next_due_date < today})
    for m in db.query(MaintenanceRecord).filter(MaintenanceRecord.user_id == user.id).all():
        if m.next_due_date:
            upcoming.append({"type": "maintenance", "title": m.title, "date": m.next_due_date.isoformat(), "amount": m.cost, "overdue": m.next_due_date < today})
    upcoming.sort(key=lambda x: x["date"])
    upcoming = upcoming[:5]

    # Recent activity (last 5 bills/obligations created)
    recent = []
    for b in bills[-5:]:
        recent.append({"type": "bill", "title": f"Bill: {b.bill_type} - {b.provider}", "date": b.created_at.isoformat() if b.created_at else None, "amount": b.amount, "status": b.status})

    return {
        "summary": {
            "due_this_week": due_this_week,
            "total_bills_month": total_bills_month,
            "properties_count": len(properties),
            "health_reminders": health_reminders,
        },
        "upcoming": upcoming,
        "recent_activity": recent,
    }