"""Maintenance router — CRUD + summary + service logs"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.models import MaintenanceRecord, ServiceLog
from app.schemas import MaintenanceCreate, MaintenanceResponse

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


@router.get("")
def list_maintenance(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(MaintenanceRecord).filter(MaintenanceRecord.user_id == user.id).order_by(MaintenanceRecord.next_due_date).all()


@router.get("/summary")
def maintenance_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    records = db.query(MaintenanceRecord).filter(MaintenanceRecord.user_id == user.id).all()
    due_this_month = sum(1 for r in records if r.next_due_date and r.next_due_date.month == date.today().month)
    completed_ytd = sum(1 for r in records if r.date_completed and r.date_completed.year == date.today().year)
    total_cost_ytd = sum(r.cost or 0 for r in records if r.date_completed and r.date_completed.year == date.today().year)
    overdue = sum(1 for r in records if r.next_due_date and r.next_due_date < date.today())
    return {"due_this_month": due_this_month, "completed_ytd": completed_ytd, "total_cost_ytd": total_cost_ytd, "overdue": overdue}


@router.post("", response_model=MaintenanceResponse)
def create_maintenance(payload: MaintenanceCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = MaintenanceRecord(user_id=user.id, **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{mid}", response_model=MaintenanceResponse)
def get_maintenance(mid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == mid, MaintenanceRecord.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Record not found")
    return obj


@router.put("/{mid}", response_model=MaintenanceResponse)
def update_maintenance(mid: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == mid, MaintenanceRecord.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Record not found")
    for k, v in payload.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{mid}")
def delete_maintenance(mid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == mid, MaintenanceRecord.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(obj)
    db.commit()
    return {"deleted": True}


@router.get("/{mid}/logs")
def service_logs(mid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == mid, MaintenanceRecord.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Record not found")
    return obj.service_logs


@router.post("/{mid}/logs")
def add_service_log(mid: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    log = ServiceLog(maintenance_id=mid, **payload)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log