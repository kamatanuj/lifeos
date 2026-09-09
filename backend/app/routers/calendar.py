"""Calendar router — unified events from all modules"""
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.models import Bill, Obligation, InsurancePolicy, MaintenanceRecord, HealthRecord, Document, HealthProfile

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

COLOR_MAP = {
    "bill": "orange",
    "obligation": "gray",
    "insurance": "blue",
    "maintenance": "green",
    "health": "purple",
    "document": "red",
}


@router.get("/events")
def calendar_events(start: str = None, end: str = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    events = []

    # Bills
    for b in db.query(Bill).filter(Bill.user_id == user.id).all():
        if b.due_date:
            events.append({"id": f"bill-{b.id}", "title": f"Bill: {b.bill_type} - {b.provider}", "date": b.due_date.isoformat(), "type": "bill", "color": COLOR_MAP["bill"], "linked_id": b.id})

    # Obligations
    for o in db.query(Obligation).filter(Obligation.user_id == user.id).all():
        if o.next_due_date:
            events.append({"id": f"obl-{o.id}", "title": o.name, "date": o.next_due_date.isoformat(), "type": "obligation", "color": COLOR_MAP["obligation"], "linked_id": o.id})

    # Insurance
    for p in db.query(InsurancePolicy).filter(InsurancePolicy.user_id == user.id).all():
        if p.renewal_date:
            events.append({"id": f"ins-{p.id}", "title": f"Insurance: {p.policy_type} - {p.provider}", "date": p.renewal_date.isoformat(), "type": "insurance", "color": COLOR_MAP["insurance"], "linked_id": p.id})

    # Maintenance
    for m in db.query(MaintenanceRecord).filter(MaintenanceRecord.user_id == user.id).all():
        if m.next_due_date:
            events.append({"id": f"maint-{m.id}", "title": m.title, "date": m.next_due_date.isoformat(), "type": "maintenance", "color": COLOR_MAP["maintenance"], "linked_id": m.id})

    # Health
    for p in db.query(HealthProfile).filter(HealthProfile.user_id == user.id).all():
        for r in p.records:
            if r.next_appointment:
                events.append({"id": f"health-{r.id}", "title": f"Health: {p.member_name} - {r.doctor or r.entry_type}", "date": r.next_appointment.isoformat(), "type": "health", "color": COLOR_MAP["health"], "linked_id": r.id})

    # Documents with expiry
    for d in db.query(Document).filter(Document.user_id == user.id).all():
        if d.expiry_date:
            events.append({"id": f"doc-{d.id}", "title": f"Doc Expiry: {d.name}", "date": d.expiry_date.isoformat(), "type": "document", "color": COLOR_MAP["document"], "linked_id": d.id})

    # Filter by date range
    if start:
        events = [e for e in events if e["date"] >= start]
    if end:
        events = [e for e in events if e["date"] <= end]

    events.sort(key=lambda x: x["date"])
    return events