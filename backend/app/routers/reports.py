"""Reports router — summary, spending breakdown"""
from datetime import date
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.models import Bill, Obligation, MaintenanceRecord, HealthRecord

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/summary")
def reports_summary(period: str = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """period format: YYYY-MM"""
    if not period:
        period = date.today().strftime("%Y-%m")
    year, month = map(int, period.split("-"))

    bills = db.query(Bill).filter(Bill.user_id == user.id).all()
    obligations = db.query(Obligation).filter(Obligation.user_id == user.id).all()
    maintenance = db.query(MaintenanceRecord).filter(MaintenanceRecord.user_id == user.id).all()
    health_records = db.query(HealthRecord).filter(HealthRecord.profile_id.in_(
        db.query(HealthRecord).join(HealthRecord.profile).filter(HealthRecord.profile.has(user_id=user.id)).subquery()
    )).all() if False else []  # Simplified - just count from health profiles

    # Spending by category
    spending = defaultdict(float)
    for b in bills:
        if b.paid_date and b.paid_date.year == year and b.paid_date.month == month:
            spending[b.bill_type] += b.paid_amount or b.amount
    for o in obligations:
        if o.last_paid_date and o.last_paid_date.year == year and o.last_paid_date.month == month:
            spending[o.category] += o.amount
    for m in maintenance:
        if m.date_completed and m.date_completed.year == year and m.date_completed.month == month:
            spending[m.type] += m.cost or 0

    total_spending = sum(spending.values())

    # Monthly trend (6 months) — bills + obligations + maintenance (actual payments only)
    trend = []
    for i in range(5, -1, -1):
        m = month - i
        y = year
        if m <= 0:
            m += 12
            y -= 1
        month_total = 0
        for b in bills:
            if b.paid_date and b.paid_date.year == y and b.paid_date.month == m:
                month_total += b.paid_amount or b.amount
        for o in obligations:
            if o.last_paid_date and o.last_paid_date.year == y and o.last_paid_date.month == m:
                month_total += o.amount
        for rec in maintenance:
            if rec.date_completed and rec.date_completed.year == y and rec.date_completed.month == m:
                month_total += rec.cost or 0
        trend.append({"month": f"{y}-{m:02d}", "amount": month_total})

    return {
        "period": period,
        "total_spending": total_spending,
        "spending_by_category": [{"category": k, "amount": v} for k, v in sorted(spending.items(), key=lambda x: -x[1])],
        "monthly_trend": trend,
    }


@router.get("/yearly")
def yearly_report(year: int = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not year:
        year = date.today().year
    bills = db.query(Bill).filter(Bill.user_id == user.id).all()
    total = sum(b.paid_amount or b.amount for b in bills if b.paid_date and b.paid_date.year == year)
    return {"year": year, "total_spending": total, "bills_count": len(bills)}