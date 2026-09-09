"""Pydantic schemas for all models"""
from datetime import datetime, date
from typing import Optional, Any
from pydantic import BaseModel, EmailStr


# ── Auth ──
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    is_active: bool
    is_2fa_enabled: bool
    created_at: datetime
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Bill ──
class BillBase(BaseModel):
    bill_type: str
    provider: str
    amount: float
    due_date: date
    payment_method: str = "upi_gpay"
    frequency: str = "monthly"
    linked_property_id: Optional[int] = None
    reminder_days_before: int = 3
    repeat_until_paid: bool = True
    notes: Optional[str] = None

class BillCreate(BillBase): pass
class BillUpdate(BaseModel):
    bill_type: Optional[str] = None
    provider: Optional[str] = None
    amount: Optional[float] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    paid_date: Optional[date] = None
    paid_amount: Optional[float] = None
    notes: Optional[str] = None

class BillResponse(BillBase):
    id: int
    user_id: int
    status: str
    paid_date: Optional[date] = None
    paid_amount: Optional[float] = None
    created_at: datetime
    class Config:
        from_attributes = True

class BillPaymentCreate(BaseModel):
    amount: float
    paid_date: date
    payment_method: Optional[str] = None
    notes: Optional[str] = None


# ── Obligation ──
class ObligationBase(BaseModel):
    name: str
    category: str
    amount: float
    frequency: str = "monthly"
    next_due_date: date
    linked_property_id: Optional[int] = None
    reminder_days_before: int = 3
    payment_method: Optional[str] = None
    repeat_until_completed: bool = True
    send_to_family: bool = False

class ObligationCreate(ObligationBase): pass

class ObligationResponse(ObligationBase):
    id: int
    user_id: int
    is_active: bool
    last_paid_date: Optional[date] = None
    created_at: datetime
    class Config:
        from_attributes = True


# ── Insurance ──
class InsuranceBase(BaseModel):
    policy_type: str
    provider: str
    policy_number: Optional[str] = None
    premium_amount: float
    renewal_date: date
    frequency: str = "yearly"
    coverage_amount: Optional[float] = None
    linked_property_id: Optional[int] = None
    coverage_details: Optional[str] = None

class InsuranceCreate(InsuranceBase): pass

class InsuranceResponse(InsuranceBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    class Config:
        from_attributes = True


# ── Property ──
class PropertyBase(BaseModel):
    name: str
    type: str
    address: Optional[str] = None
    ownership_type: str = "owned"
    purchase_date: Optional[date] = None
    society_name: Optional[str] = None
    secretary_name: Optional[str] = None
    secretary_phone: Optional[str] = None
    maintenance_contact: Optional[str] = None
    maintenance_phone: Optional[str] = None
    insurance_amount: Optional[float] = None
    maintenance_amount: Optional[float] = None
    society_fee: Optional[float] = None
    society_fee_frequency: str = "monthly"
    rental_amount: Optional[float] = None
    rental_agreement_expiry: Optional[date] = None

class PropertyCreate(PropertyBase): pass

class PropertyResponse(PropertyBase):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ── Maintenance ──
class MaintenanceBase(BaseModel):
    type: str
    title: str
    property_id: Optional[int] = None
    service_provider: Optional[str] = None
    cost: Optional[float] = None
    date_completed: Optional[date] = None
    next_due_date: Optional[date] = None
    frequency: Optional[str] = None
    notes: Optional[str] = None

class MaintenanceCreate(MaintenanceBase): pass

class MaintenanceResponse(MaintenanceBase):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ── Health ──
class HealthProfileBase(BaseModel):
    member_name: str
    member_relationship: str
    blood_group: Optional[str] = None
    breed: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None

class HealthProfileCreate(HealthProfileBase): pass

class HealthProfileResponse(HealthProfileBase):
    id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class HealthRecordBase(BaseModel):
    entry_type: str
    date: date
    doctor: Optional[str] = None
    hospital: Optional[str] = None
    diagnosis: Optional[str] = None
    medications: Optional[str] = None
    next_appointment: Optional[date] = None
    notes: Optional[str] = None

class HealthRecordCreate(HealthRecordBase): pass

class HealthRecordResponse(HealthRecordBase):
    id: int
    profile_id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ── Document ──
class DocumentBase(BaseModel):
    name: str
    category: str
    linked_type: Optional[str] = None
    linked_id: Optional[int] = None
    tags: list = []
    expiry_date: Optional[date] = None
    notes: Optional[str] = None

class DocumentCreate(DocumentBase): pass

class DocumentResponse(DocumentBase):
    id: int
    user_id: int
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: datetime
    class Config:
        from_attributes = True


# ── Notification ──
class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    message: Optional[str] = None
    linked_module: Optional[str] = None
    linked_id: Optional[int] = None
    is_read: bool
    created_at: datetime
    class Config:
        from_attributes = True