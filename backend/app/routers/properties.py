"""Properties router — CRUD + sub-resources (maintenance, tax, insurance, rental)"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.models import Property, PropertyMaintenance, PropertyTax, PropertyInsurance, PropertyRental
from app.schemas import PropertyCreate, PropertyResponse

router = APIRouter(prefix="/api/properties", tags=["properties"])


@router.get("")
def list_properties(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Property).filter(Property.user_id == user.id).all()


@router.post("", response_model=PropertyResponse)
def create_property(payload: PropertyCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = Property(user_id=user.id, **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{pid}", response_model=PropertyResponse)
def get_property(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(Property).filter(Property.id == pid, Property.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Property not found")
    return obj


@router.put("/{pid}", response_model=PropertyResponse)
def update_property(pid: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(Property).filter(Property.id == pid, Property.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Property not found")
    for k, v in payload.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{pid}")
def delete_property(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.query(Property).filter(Property.id == pid, Property.user_id == user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Property not found")
    db.delete(obj)
    db.commit()
    return {"deleted": True}


# ── Sub-resources ──
@router.get("/{pid}/maintenance")
def property_maintenance(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    prop = db.query(Property).filter(Property.id == pid, Property.user_id == user.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop.maintenance


@router.post("/{pid}/maintenance")
def add_maintenance(pid: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = PropertyMaintenance(property_id=pid, **payload)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.get("/{pid}/tax")
def property_tax(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    prop = db.query(Property).filter(Property.id == pid, Property.user_id == user.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop.taxes


@router.get("/{pid}/insurance")
def property_insurance(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    prop = db.query(Property).filter(Property.id == pid, Property.user_id == user.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop.property_insurance


@router.get("/{pid}/rental")
def property_rental(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    prop = db.query(Property).filter(Property.id == pid, Property.user_id == user.id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop.rental