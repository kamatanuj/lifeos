"""All LifeOS models — User, Bills, Obligations, Insurance, Properties, Maintenance, Health, Documents, Notifications"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Float, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_2fa_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    bills = relationship("Bill", back_populates="user", cascade="all, delete-orphan")
    obligations = relationship("Obligation", back_populates="user", cascade="all, delete-orphan")
    insurance_policies = relationship("InsurancePolicy", back_populates="user", cascade="all, delete-orphan")
    properties = relationship("Property", back_populates="user", cascade="all, delete-orphan")
    maintenance_records = relationship("MaintenanceRecord", back_populates="user", cascade="all, delete-orphan")
    health_profiles = relationship("HealthProfile", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bill_type = Column(String(50), nullable=False)  # electricity, mobile, internet, credit_card, water, gas, other
    provider = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    payment_method = Column(String(50), default="upi_gpay")
    frequency = Column(String(50), default="monthly")  # one_time, monthly, quarterly, half_yearly, yearly
    linked_property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    reminder_days_before = Column(Integer, default=3)
    repeat_until_paid = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, paid, overdue
    paid_date = Column(Date, nullable=True)
    paid_amount = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="bills")
    linked_property = relationship("Property", foreign_keys=[linked_property_id])
    payments = relationship("BillPayment", back_populates="bill", cascade="all, delete-orphan")


class BillPayment(Base):
    __tablename__ = "bill_payments"
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    paid_date = Column(Date, nullable=False)
    payment_method = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    bill = relationship("Bill", back_populates="payments")


class Obligation(Base):
    __tablename__ = "obligations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # loan, emi, rent, subscription, insurance_premium, other
    amount = Column(Float, nullable=False)
    frequency = Column(String(50), default="monthly")
    next_due_date = Column(Date, nullable=False)
    linked_property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    reminder_days_before = Column(Integer, default=3)
    payment_method = Column(String(50), nullable=True)
    repeat_until_completed = Column(Boolean, default=True)
    send_to_family = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_paid_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="obligations")
    linked_property = relationship("Property", foreign_keys=[linked_property_id])
    payments = relationship("ObligationPayment", back_populates="obligation", cascade="all, delete-orphan")


class ObligationPayment(Base):
    __tablename__ = "obligation_payments"
    id = Column(Integer, primary_key=True, index=True)
    obligation_id = Column(Integer, ForeignKey("obligations.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    paid_date = Column(Date, nullable=False)
    method = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    obligation = relationship("Obligation", back_populates="payments")


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    policy_type = Column(String(100), nullable=False)  # health, life, vehicle, home, travel, other
    provider = Column(String(255), nullable=False)
    policy_number = Column(String(255), nullable=True)
    premium_amount = Column(Float, nullable=False)
    renewal_date = Column(Date, nullable=False)
    frequency = Column(String(50), default="yearly")
    coverage_amount = Column(Float, nullable=True)
    linked_property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    coverage_details = Column(Text, nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    status = Column(String(50), default="active")  # active, lapsed, cancelled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="insurance_policies")
    linked_property = relationship("Property", foreign_keys=[linked_property_id])


class Property(Base):
    __tablename__ = "properties"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # apartment, house, plot, commercial, vehicle
    address = Column(Text, nullable=True)
    ownership_type = Column(String(50), default="owned")  # owned, rented, leased
    purchase_date = Column(Date, nullable=True)
    society_name = Column(String(255), nullable=True)
    secretary_name = Column(String(255), nullable=True)
    secretary_phone = Column(String(50), nullable=True)
    maintenance_contact = Column(String(255), nullable=True)
    maintenance_phone = Column(String(50), nullable=True)
    insurance_amount = Column(Float, nullable=True)
    maintenance_amount = Column(Float, nullable=True)
    society_fee = Column(Float, nullable=True)
    society_fee_frequency = Column(String(50), default="monthly")
    rental_amount = Column(Float, nullable=True)
    rental_agreement_expiry = Column(Date, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="properties")
    maintenance = relationship("PropertyMaintenance", back_populates="property", cascade="all, delete-orphan")
    taxes = relationship("PropertyTax", back_populates="property", cascade="all, delete-orphan")
    property_insurance = relationship("PropertyInsurance", back_populates="property", cascade="all, delete-orphan")
    rental = relationship("PropertyRental", back_populates="property", cascade="all, delete-orphan", uselist=False)


class PropertyMaintenance(Base):
    __tablename__ = "property_maintenance"
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    cost = Column(Float, nullable=True)
    date = Column(Date, nullable=True)
    next_due_date = Column(Date, nullable=True)
    frequency = Column(String(50), nullable=True)

    property = relationship("Property", back_populates="maintenance")


class PropertyTax(Base):
    __tablename__ = "property_tax"
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    paid_date = Column(Date, nullable=True)
    receipt_document_id = Column(Integer, nullable=True)

    property = relationship("Property", back_populates="taxes")


class PropertyInsurance(Base):
    __tablename__ = "property_insurance"
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(255), nullable=True)
    policy_number = Column(String(255), nullable=True)
    premium = Column(Float, nullable=True)
    renewal_date = Column(Date, nullable=True)

    property = relationship("Property", back_populates="property_insurance")


class PropertyRental(Base):
    __tablename__ = "property_rental"
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, unique=True)
    tenant_name = Column(String(255), nullable=True)
    rent_amount = Column(Float, nullable=True)
    agreement_start = Column(Date, nullable=True)
    agreement_end = Column(Date, nullable=True)
    document_id = Column(Integer, nullable=True)

    property = relationship("Property", back_populates="rental")


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(100), nullable=False)  # car_service, home_repair, appliance, pest_control, other
    title = Column(String(255), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    vehicle_id = Column(Integer, nullable=True)
    service_provider = Column(String(255), nullable=True)
    cost = Column(Float, nullable=True)
    date_completed = Column(Date, nullable=True)
    next_due_date = Column(Date, nullable=True)
    frequency = Column(String(50), nullable=True)  # one_time, monthly, quarterly, half_yearly, yearly, mileage_based
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="maintenance_records")
    property = relationship("Property", foreign_keys=[property_id])
    service_logs = relationship("ServiceLog", back_populates="maintenance", cascade="all, delete-orphan")


class ServiceLog(Base):
    __tablename__ = "service_logs"
    id = Column(Integer, primary_key=True, index=True)
    maintenance_id = Column(Integer, ForeignKey("maintenance_records.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    odometer_reading = Column(Integer, nullable=True)
    services_performed = Column(Text, nullable=True)
    cost = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    maintenance = relationship("MaintenanceRecord", back_populates="service_logs")


class HealthProfile(Base):
    __tablename__ = "health_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    member_name = Column(String(255), nullable=False)
    member_relationship = Column(String(50), nullable=False)  # self, mother, father, brother, sister, spouse, child, pet
    blood_group = Column(String(10), nullable=True)
    breed = Column(String(255), nullable=True)  # for pets
    allergies = Column(Text, nullable=True)
    chronic_conditions = Column(Text, nullable=True)
    insurance_provider = Column(String(255), nullable=True)
    insurance_number = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="health_profiles")
    records = relationship("HealthRecord", back_populates="profile", cascade="all, delete-orphan")


class HealthRecord(Base):
    __tablename__ = "health_records"
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("health_profiles.id", ondelete="CASCADE"), nullable=False)
    entry_type = Column(String(50), nullable=False)  # doctor_visit, prescription, lab_test, vaccination, diagnosis, surgery, imaging, allergy
    date = Column(Date, nullable=False)
    doctor = Column(String(255), nullable=True)
    hospital = Column(String(255), nullable=True)
    diagnosis = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    next_appointment = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    profile = relationship("HealthProfile", back_populates="records")
    documents = relationship("HealthDocument", back_populates="record", cascade="all, delete-orphan")


class HealthDocument(Base):
    __tablename__ = "health_documents"
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("health_records.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(String(100), nullable=True)
    file_path = Column(String(500), nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    record = relationship("HealthRecord", back_populates="documents")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # insurance, property, identity, medical, tax, bank, warranty, amc, receipt, invoice
    linked_type = Column(String(50), nullable=True)
    linked_id = Column(Integer, nullable=True)
    file_path = Column(String(500), nullable=True)  # storage path
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)
    expiry_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="documents")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # overdue, reminder, activity, info
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    linked_module = Column(String(50), nullable=True)
    linked_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="notifications")