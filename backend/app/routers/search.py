"""Search router — global search across all modules"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.models import Bill, Obligation, InsurancePolicy, Property, MaintenanceRecord, HealthProfile, HealthRecord, Document

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search(q: str = "", category: str = "all", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not q:
        return {"results": []}

    results = []
    uid = user.id
    pattern = f"%{q}%"

    if category in ("all", "bills"):
        for b in db.query(Bill).filter(Bill.user_id == uid, or_(Bill.provider.ilike(pattern), Bill.bill_type.ilike(pattern), Bill.notes.ilike(pattern))).all():
            results.append({"type": "bill", "id": b.id, "title": f"{b.bill_type} - {b.provider}", "snippet": f"₹{b.amount} due {b.due_date}", "date": b.due_date.isoformat() if b.due_date else None})

    if category in ("all", "obligations"):
        for o in db.query(Obligation).filter(Obligation.user_id == uid, or_(Obligation.name.ilike(pattern), Obligation.category.ilike(pattern))).all():
            results.append({"type": "obligation", "id": o.id, "title": o.name, "snippet": f"₹{o.amount} {o.frequency}", "date": o.next_due_date.isoformat() if o.next_due_date else None})

    if category in ("all", "insurance"):
        for p in db.query(InsurancePolicy).filter(InsurancePolicy.user_id == uid, or_(InsurancePolicy.provider.ilike(pattern), InsurancePolicy.policy_type.ilike(pattern), InsurancePolicy.policy_number.ilike(pattern))).all():
            results.append({"type": "insurance", "id": p.id, "title": f"{p.policy_type} - {p.provider}", "snippet": f"₹{p.premium_amount} renewal {p.renewal_date}", "date": p.renewal_date.isoformat() if p.renewal_date else None})

    if category in ("all", "properties"):
        for p in db.query(Property).filter(Property.user_id == uid, or_(Property.name.ilike(pattern), Property.address.ilike(pattern), Property.society_name.ilike(pattern))).all():
            results.append({"type": "property", "id": p.id, "title": p.name, "snippet": p.address or "", "date": None})

    if category in ("all", "maintenance"):
        for m in db.query(MaintenanceRecord).filter(MaintenanceRecord.user_id == uid, or_(MaintenanceRecord.title.ilike(pattern), MaintenanceRecord.service_provider.ilike(pattern), MaintenanceRecord.notes.ilike(pattern))).all():
            results.append({"type": "maintenance", "id": m.id, "title": m.title, "snippet": m.service_provider or "", "date": m.next_due_date.isoformat() if m.next_due_date else None})

    if category in ("all", "health"):
        for p in db.query(HealthProfile).filter(HealthProfile.user_id == uid, or_(HealthProfile.member_name.ilike(pattern), HealthProfile.chronic_conditions.ilike(pattern), HealthProfile.allergies.ilike(pattern))).all():
            results.append({"type": "health", "id": p.id, "title": p.member_name, "snippet": f"{p.relationship} - {p.blood_group or ''}", "date": None})

    if category in ("all", "documents"):
        for d in db.query(Document).filter(Document.user_id == uid, or_(Document.name.ilike(pattern), Document.notes.ilike(pattern))).all():
            results.append({"type": "document", "id": d.id, "title": d.name, "snippet": d.category, "date": d.expiry_date.isoformat() if d.expiry_date else None})

    return {"results": results, "count": len(results)}