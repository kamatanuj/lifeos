"""Voice agent tool dispatch router — handles all Dograh tool calls"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User, Bill, Obligation, InsurancePolicy, Property, MaintenanceRecord, HealthProfile, HealthRecord, Document
from app.routers.voice_ws import push_navigation
from app.utils.natural_dates import resolve_date_range, resolve_single_date
from starlette.requests import Request as StarletteRequest

router = APIRouter(prefix="/api/voice", tags=["voice-agent"])

import os as _os
API_KEY = _os.getenv("LIFEOS_VOICE_API_KEY", "lifeos_dograh_2026")


def _check_auth(x_api_key: str = Header(None, alias="X-API-Key"), db: Session = Depends(get_db)) -> User:
    if x_api_key and x_api_key == API_KEY:
        user = db.query(User).first()
        if user:
            return user
    raise HTTPException(status_code=401, detail="Invalid API key")


# Screen name → data endpoint mapping
# Note: health uses HealthProfile (has user_id), HealthRecord uses profile_id
SCREEN_TABLES = {
    "bills": Bill,
    "obligations": Obligation,
    "insurance": InsurancePolicy,
    "properties": Property,
    "maintenance": MaintenanceRecord,
    "health": HealthProfile,  # HealthProfile has user_id, HealthRecord doesn't
    "documents": Document,
}


@router.get("/navigate")
def navigate_screen(request: StarletteRequest, db: Session = Depends(get_db), user: User = Depends(_check_auth)):
    """Navigate to any LifeOS screen — returns screen metadata and summary data.

    Accepts the target screen from any common param name (screen, name, to, target, page,
    destination) so agents that misname the argument still work."""
    params = dict(request.query_params)
    screen = None
    for key in ("screen", "name", "to", "target", "page", "destination", "destination_screen", "screen_name"):
        val = (params.get(key) or "").strip()
        if val:
            screen = val
            break
    if not screen:
        return {"error": "Missing screen name. Tell me which screen, e.g. bills, obligations, dashboard.", "valid_screens": ["dashboard","calendar","search","bills","obligations","insurance","properties","maintenance","health","documents","reports","settings","users","bill-new","obligation-new","insurance-new","property-new","maintenance-new","health-new","document-new"]}
    screen = screen.lower().strip()
    
    # Form screens return form metadata
    form_screens = {
        "bill-new": {"screen": "bill-new", "type": "form", "title": "Add New Bill", "fields": ["bill_type", "provider", "amount", "due_date", "payment_method", "frequency", "notes"]},
        "obligation-new": {"screen": "obligation-new", "type": "form", "title": "Add New Obligation", "fields": ["name", "category", "amount", "frequency", "next_due_date", "notes"]},
        "insurance-new": {"screen": "insurance-new", "type": "form", "title": "Add New Insurance Policy", "fields": ["policy_type", "provider", "policy_number", "premium_amount", "renewal_date", "coverage_amount", "status"]},
        "property-new": {"screen": "property-new", "type": "form", "title": "Add New Property", "fields": ["name", "property_type", "address", "ownership_type", "society_name", "purchase_date", "society_fee", "rental_amount"]},
        "maintenance-new": {"screen": "maintenance-new", "type": "form", "title": "Add Maintenance Record", "fields": ["title", "service_provider", "cost", "next_due_date", "frequency", "notes"]},
        "health-new": {"screen": "health-new", "type": "form", "title": "Add Health Profile", "fields": ["member_name", "member_relationship", "blood_group", "allergies", "chronic_conditions"]},
        "document-new": {"screen": "document-new", "type": "form", "title": "Add Document", "fields": ["name", "category", "expiry_date", "notes"]},
    }
    
    if screen in form_screens:
        push_navigation(screen, "navigate", form_screens[screen])
        return form_screens[screen]
    
    # Regular screens return summary data
    today = date.today()
    
    if screen == "dashboard":
        bills = db.query(Bill).filter(Bill.user_id == user.id).all()
        obligations = db.query(Obligation).filter(Obligation.user_id == user.id, Obligation.is_active == True).all()
        properties = db.query(Property).filter(Property.user_id == user.id).all()
        health_profiles = db.query(HealthProfile).filter(HealthProfile.user_id == user.id).all()
        week_later = today + timedelta(days=7)
        due_this_week = sum(1 for b in bills if b.status == "pending" and b.due_date and today <= b.due_date <= week_later)
        result = {
            "screen": "dashboard",
            "type": "dashboard",
            "summary": {
                "due_this_week": due_this_week,
                "total_bills_month": sum(b.amount for b in bills if b.due_date and b.due_date.month == today.month),
                "properties_count": len(properties),
                "health_reminders": sum(1 for p in health_profiles for r in p.records if r.next_appointment and today <= r.next_appointment <= week_later),
            },
            "upcoming": [{"type": "bill", "title": f"{b.bill_type} - {b.provider}", "date": b.due_date.isoformat(), "amount": b.amount, "overdue": b.due_date < today} for b in bills if b.status == "pending" and b.due_date][:5],
        }
        push_navigation("dashboard", "navigate", result)
        return result
    
    elif screen in SCREEN_TABLES:
        model = SCREEN_TABLES[screen]
        items = db.query(model).filter(getattr(model, "user_id") == user.id).all()
        result = {
            "screen": screen,
            "type": "table",
            "count": len(items),
            "items": [_serialize(item) for item in items[:20]],
        }
        push_navigation(screen, "navigate", result)
        return result
    
    elif screen == "calendar":
        bills = db.query(Bill).filter(Bill.user_id == user.id).all()
        obligations = db.query(Obligation).filter(Obligation.user_id == user.id).all()
        events = []
        for b in bills:
            if b.due_date:
                events.append({"date": b.due_date.isoformat(), "type": "bill", "title": f"{b.bill_type} - {b.provider}", "amount": b.amount})
        for o in obligations:
            if o.next_due_date:
                events.append({"date": o.next_due_date.isoformat(), "type": "obligation", "title": o.name, "amount": o.amount})
        events.sort(key=lambda x: x["date"])
        result = {"screen": "calendar", "type": "calendar", "events": events[:30]}
        push_navigation("calendar", "navigate", result)
        return result
    
    elif screen == "reports":
        result = {"screen": "reports", "type": "reports", "message": "Use show_report tool with from_date and to_date to get report data."}
        # Don't push nav for reports — show_report endpoint pushes with period data
        return result
    
    elif screen == "search":
        result = {"screen": "search", "type": "search", "message": "Use search_items tool with a query parameter."}
        push_navigation("search", "navigate", result)
        return result
    
    elif screen == "settings":
        result = {"screen": "settings", "type": "settings"}
        push_navigation("settings", "navigate", result)
        return result
    
    return {"screen": screen, "error": f"Unknown screen: {screen}"}


@router.get("/report")
def show_report(from_date: str = Query(None), to_date: str = Query(None), report_type: str = Query("all"), db: Session = Depends(get_db), user: User = Depends(_check_auth)):
    """Get report data for a date range — accepts natural language like 'July to August'."""
    # Natural-language range parsing: "july to august", "this month", "last 3 months",
    # "for july", "march 2025 to august 2025" — YYYY-MM-DD also still accepted.
    if from_date and to_date:
        start, end, dreason = None, None, None
        try:
            start = date.fromisoformat(from_date[:10])
            end = date.fromisoformat(to_date[:10])
        except (ValueError, TypeError):
            start, end = resolve_date_range(f"{from_date} to {to_date}")
        if not start or not end:
            return {"error": f"Invalid date range. from={from_date}, to={to_date}" + (f" ({dreason})" if dreason else "")}
    else:
        # No explicit dates: parse the range from either param (the workflow passes
        # the spoken phrase through) or report_type when it carries the phrase.
        phrase = from_date or to_date or report_type
        if phrase in ("all", "reports", None) or not phrase:
            return {"error": "Tell me the period, e.g. 'report for July' or 'July to August'.", "needs_date": True}
        start, end = resolve_date_range(phrase)
        if not start or not end:
            return {"error": str(end), "needs_date": True}
    
    bills = db.query(Bill).filter(Bill.user_id == user.id).all()
    maintenance = db.query(MaintenanceRecord).filter(MaintenanceRecord.user_id == user.id).all()
    obligations = db.query(Obligation).filter(Obligation.user_id == user.id).all()
    
    # Filter by date range
    period_bills = [b for b in bills if b.due_date and start <= b.due_date <= end]
    period_maintenance = [m for m in maintenance if m.next_due_date and start <= m.next_due_date <= end]
    period_obligations = [o for o in obligations if o.next_due_date and start <= o.next_due_date <= end]
    
    total_spending = sum(b.amount for b in period_bills) + sum(m.cost for m in period_maintenance) + sum(o.amount for o in period_obligations)
    
    # Category breakdown
    categories = {}
    for b in period_bills:
        cat = b.bill_type or "other"
        categories[cat] = categories.get(cat, 0) + b.amount
    for m in period_maintenance:
        categories["maintenance"] = categories.get("maintenance", 0) + m.cost
    for o in period_obligations:
        cat = o.category or "obligation"
        categories[cat] = categories.get(cat, 0) + o.amount
    
    # Monthly trend
    monthly = {}
    for b in period_bills:
        key = b.due_date.strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0) + b.amount
    
    result = {
        "screen": "reports",
        "period": {"from": start.isoformat(), "to": end.isoformat(),
                   "spoken": from_date or to_date or report_type},
        "total_spending": total_spending,
        "spending_by_category": categories,
        "monthly_trend": monthly,
        "bill_count": len(period_bills),
        "maintenance_count": len(period_maintenance),
        "obligation_count": len(period_obligations),
        "bills": [_serialize(b) for b in period_bills[:20]],
    }
    push_navigation("reports", "navigate", result)
    return result


@router.get("/search")
def search_items(query: str = Query(...), category: str = Query("all"), db: Session = Depends(get_db), user: User = Depends(_check_auth)):
    """Search across all LifeOS data"""
    q = query.lower()
    results = []
    
    # Search bills
    if category in ("all", "bills"):
        for b in db.query(Bill).filter(Bill.user_id == user.id).all():
            text = f"{b.bill_type} {b.provider} {b.notes or ''}".lower()
            if q in text:
                results.append({"type": "bill", "id": b.id, "title": f"{b.bill_type} - {b.provider}", "amount": b.amount, "due_date": b.due_date.isoformat() if b.due_date else None, "status": b.status})
    
    # Search obligations
    if category in ("all", "obligations"):
        for o in db.query(Obligation).filter(Obligation.user_id == user.id).all():
            text = f"{o.name} {o.category or ''}".lower()
            if q in text:
                results.append({"type": "obligation", "id": o.id, "title": o.name, "amount": o.amount, "next_due": o.next_due_date.isoformat() if o.next_due_date else None})
    
    # Search insurance
    if category in ("all", "insurance"):
        for p in db.query(InsurancePolicy).filter(InsurancePolicy.user_id == user.id).all():
            text = f"{p.provider} {p.provider} {p.policy_type}".lower()
            if q in text:
                results.append({"type": "insurance", "id": p.id, "title": f"{p.provider} - {p.provider}", "premium": p.premium_amount, "status": p.status})
    
    # Search properties
    if category in ("all", "properties"):
        for p in db.query(Property).filter(Property.user_id == user.id).all():
            text = f"{p.name} {p.address or ''}".lower()
            if q in text:
                results.append({"type": "property", "id": p.id, "title": p.name, "value": p.current_value, "address": p.address})
    
    # Search maintenance
    if category in ("all", "maintenance"):
        for m in db.query(MaintenanceRecord).filter(MaintenanceRecord.user_id == user.id).all():
            text = f"{m.title} {m.notes or ''}".lower()
            if q in text:
                results.append({"type": "maintenance", "id": m.id, "title": m.title, "cost": m.cost, "status": "completed" if m.date_completed else "pending"})
    
    # Search documents
    if category in ("all", "documents"):
        for d in db.query(Document).filter(Document.user_id == user.id).all():
            text = f"{d.name} {d.category or ''}".lower()
            if q in text:
                results.append({"type": "document", "id": d.id, "title": d.name, "category": d.category})
    
    result = {"screen": "search", "query": query, "count": len(results), "results": results[:20]}
    push_navigation("search", "navigate", result)
    return result


@router.get("/read-table")
def read_table(screen: str = Query(...), filter: str = Query(None), db: Session = Depends(get_db), user: User = Depends(_check_auth)):
    """Read data from a specific screen's table, optionally filtered"""
    screen = screen.lower().strip()
    if screen not in SCREEN_TABLES:
        return {"error": f"Invalid screen: {screen}. Valid: {list(SCREEN_TABLES.keys())}"}
    
    model = SCREEN_TABLES[screen]
    items = db.query(model).filter(getattr(model, "user_id") == user.id).all()
    
    # Apply filter
    if filter:
        filter_lower = filter.lower()
        if screen == "bills":
            if filter_lower == "overdue":
                items = [b for b in items if b.status == "pending" and b.due_date and b.due_date < date.today()]
            elif filter_lower == "paid":
                items = [b for b in items if b.status == "paid"]
            elif filter_lower == "upcoming":
                items = [b for b in items if b.status == "pending" and b.due_date and b.due_date >= date.today()]
            else:
                items = [b for b in items if filter_lower in f"{b.bill_type} {b.provider} {b.notes or ''}".lower()]
        elif screen == "obligations":
            if filter_lower == "active":
                items = [o for o in items if o.is_active]
            else:
                items = [o for o in items if filter_lower in f"{o.name} {o.category or ''}".lower()]
        elif screen == "maintenance":
            if filter_lower == "pending":
                items = [m for m in items if m.date_completed is None]
            elif filter_lower == "completed":
                items = [m for m in items if m.date_completed is not None]
            elif filter_lower == "overdue":
                items = [m for m in items if m.date_completed is None and m.next_due_date and m.next_due_date < today]
            else:
                items = [m for m in items if filter_lower in f"{m.title} {m.notes or ''}".lower()]
        elif screen == "insurance":
            if filter_lower in ("active", "lapsed", "expired"):
                items = [p for p in items if p.status and filter_lower in p.status.lower()]
            else:
                items = [p for p in items if filter_lower in f"{p.provider} {p.provider} {p.policy_type}".lower()]
        else:
            items = [i for i in items if filter_lower in str(_serialize(i)).lower()]
    
    result = {
        "screen": screen,
        "filter": filter or "none",
        "count": len(items),
        "items": [_serialize(item) for item in items[:20]],
    }
    if screen == "reports":
        # Don't push nav for reports — show_report endpoint pushes with period data
        result = {"screen": "reports", "type": "reports", "message": "Use show_report tool with from_date and to_date to get report data."}
        return result
    
    push_navigation(screen, "navigate", result)
    return result


@router.get("/summary")
def get_summary(summary_type: str = Query(...), db: Session = Depends(get_db), user: User = Depends(_check_auth)):
    """Get summary cards from dashboard or specific screen"""
    stype = summary_type.lower().strip()
    today = date.today()
    week_later = today + timedelta(days=7)
    
    bills = db.query(Bill).filter(Bill.user_id == user.id).all()
    obligations = db.query(Obligation).filter(Obligation.user_id == user.id).all()
    properties = db.query(Property).filter(Property.user_id == user.id).all()
    maintenance = db.query(MaintenanceRecord).filter(MaintenanceRecord.user_id == user.id).all()
    health_profiles = db.query(HealthProfile).filter(HealthProfile.user_id == user.id).all()
    insurance = db.query(InsurancePolicy).filter(InsurancePolicy.user_id == user.id).all()
    
    if stype == "spending":
        month_bills = sum(b.amount for b in bills if b.due_date and b.due_date.month == today.month)
        last_month = today.month - 1 or 12
        last_month_bills = sum(b.amount for b in bills if b.due_date and b.due_date.month == last_month)
        return {
            "summary_type": "spending",
            "this_month": month_bills,
            "last_month": last_month_bills,
            "change_pct": round(((month_bills - last_month_bills) / last_month_bills * 100) if last_month_bills else 0, 1),
            "bill_count": len(bills),
        }
    
    elif stype == "bills":
        pending = [b for b in bills if b.status == "pending"]
        overdue = [b for b in pending if b.due_date and b.due_date < today]
        due_week = [b for b in pending if b.due_date and today <= b.due_date <= week_later]
        return {
            "summary_type": "bills",
            "total": len(bills),
            "pending": len(pending),
            "overdue": len(overdue),
            "due_this_week": len(due_week),
            "overdue_items": [{"title": f"{b.bill_type} - {b.provider}", "amount": b.amount, "due_date": b.due_date.isoformat()} for b in overdue],
        }
    
    elif stype == "maintenance":
        pending = [m for m in maintenance if m.date_completed is None]
        overdue = [m for m in pending if m.next_due_date and m.next_due_date < today]
        return {
            "summary_type": "maintenance",
            "total": len(maintenance),
            "pending": len(pending),
            "overdue": len(overdue),
            "total_cost": sum(m.cost for m in maintenance),
        }
    
    elif stype == "insurance":
        active = [p for p in insurance if p.status == "active"]
        return {
            "summary_type": "insurance",
            "total_policies": len(insurance),
            "active": len(active),
            "total_premium": sum(p.premium_amount for p in active if p.premium_amount),
            "total_coverage": sum(p.coverage_amount for p in active if p.coverage_amount),
        }
    
    # "all" — full dashboard
    return {
        "summary_type": "all",
        "due_this_week": sum(1 for b in bills if b.status == "pending" and b.due_date and today <= b.due_date <= week_later),
        "total_bills_month": sum(b.amount for b in bills if b.due_date and b.due_date.month == today.month),
        "properties_count": len(properties),
        "health_reminders": sum(1 for p in health_profiles for r in p.records if r.next_appointment and today <= r.next_appointment <= week_later),
        "bills_pending": sum(1 for b in bills if b.status == "pending"),
        "bills_overdue": sum(1 for b in bills if b.status == "pending" and b.due_date and b.due_date < today),
        "obligations_active": sum(1 for o in obligations if o.is_active),
        "maintenance_pending": sum(1 for m in maintenance if m.date_completed is None),
        "insurance_active": sum(1 for p in insurance if p.status == "active"),
    }


@router.get("/click-item")
def click_item(screen: str = Query(...), item_name: str = Query(...), db: Session = Depends(get_db), user: User = Depends(_check_auth)):
    """Find and return a specific item by name/provider match"""
    screen = screen.lower().strip()
    item_name = item_name.lower().strip()
    
    if screen not in SCREEN_TABLES:
        return {"error": f"Invalid screen: {screen}"}
    
    model = SCREEN_TABLES[screen]
    items = db.query(model).filter(getattr(model, "user_id") == user.id).all()
    
    matches = []
    for item in items:
        serialized = _serialize(item)
        text = str(serialized).lower()
        if item_name in text:
            matches.append(serialized)
    
    if matches:
        return {"screen": screen, "item_name": item_name, "found": True, "count": len(matches), "items": matches[:5]}
    return {"screen": screen, "item_name": item_name, "found": False, "message": f"No items matching '{item_name}' in {screen}"}


# ─── Form field mappings: voice-friendly names → DB columns ───
SCREEN_FORM_FIELDS = {
    "bills": {
        "model": Bill,
        "fields": {
            "bill_type": "bill_type",
            "type": "bill_type",
            "provider": "provider",
            "amount": "amount",
            "due_date": "due_date",
            "payment_method": "payment_method",
            "frequency": "frequency",
            "notes": "notes",
        },
        "defaults": {"status": "pending", "repeat_until_paid": True, "reminder_days_before": 3},
        "nav_screen": "bills",
    },
    "obligations": {
        "model": Obligation,
        "fields": {
            "name": "name",
            "category": "category",
            "amount": "amount",
            "frequency": "frequency",
            "next_due_date": "next_due_date",
        },
        "defaults": {"is_active": True, "repeat_until_completed": True, "reminder_days_before": 3},
        "nav_screen": "obligations",
    },
    "insurance": {
        "model": InsurancePolicy,
        "fields": {
            "policy_type": "policy_type",
            "policy_name": "policy_type",
            "provider": "provider",
            "policy_number": "policy_number",
            "premium_amount": "premium_amount",
            "premium": "premium_amount",
            "renewal_date": "renewal_date",
            "coverage_amount": "coverage_amount",
            "status": "status",
        },
        "defaults": {"status": "active", "frequency": "yearly"},
        "nav_screen": "insurance",
    },
    "properties": {
        "model": Property,
        "fields": {
            "name": "name",
            "property_type": "type",
            "type": "type",
            "type_of_property": "type",
            "address": "address",
            "ownership_type": "ownership_type",
            "society_name": "society_name",
            "purchase_date": "purchase_date",
            "society_fee": "society_fee",
            "rental_amount": "rental_amount",
            "insurance_amount": "insurance_amount",
            "maintenance_amount": "maintenance_amount",
        },
        "defaults": {},
        "nav_screen": "properties",
    },
    "maintenance": {
        "model": MaintenanceRecord,
        "fields": {
            "type": "type",
            "title": "title",
            "description": "notes",
            "service_provider": "service_provider",
            "cost": "cost",
            "next_due_date": "next_due_date",
            "frequency": "frequency",
            "date_completed": "date_completed",
            "notes": "notes",
        },
        "defaults": {},
        "nav_screen": "maintenance",
    },
    "health": {
        "model": HealthProfile,
        "fields": {
            "member_name": "member_name",
            "profile_name": "member_name",
            "member_relationship": "member_relationship",
            "blood_group": "blood_group",
            "allergies": "allergies",
            "chronic_conditions": "chronic_conditions",
            "insurance_provider": "insurance_provider",
        },
        "defaults": {},
        "nav_screen": "health",
    },
    "documents": {
        "model": Document,
        "fields": {
            "name": "name",
            "title": "name",
            "category": "category",
            "expiry_date": "expiry_date",
            "notes": "notes",
        },
        "defaults": {"file_path": "", "file_size": 0, "mime_type": "text/plain"},
        "nav_screen": "documents",
    },
}

# DB NOT-NULL fields the voice agent must supply for create (validated pre-insert
# so the agent gets a precise, self-explanatory error instead of a SQL exception).
# maintenance "type" is omitted — it auto-derives from the title.
REQUIRED_FIELDS = {
    "bills": ["bill_type", "provider", "amount", "due_date"],
    "obligations": ["name", "category", "amount", "next_due_date"],
    "insurance": ["policy_type", "provider", "premium_amount", "renewal_date"],
    "properties": ["name", "type"],
    "maintenance": ["title"],
    "health": ["member_name", "member_relationship"],
    "documents": ["name", "category"],
}


def _infer_property_type(text: str) -> str:
    """Guess property type from the spoken name/description."""
    t = (text or "").lower()
    if any(w in t for w in ("flat", "apartment", "apt")):
        return "apartment"
    if any(w in t for w in ("house", "villa", "bungalow", "home")):
        return "house"
    if any(w in t for w in ("plot", "land", "site")):
        return "plot"
    if any(w in t for w in ("shop", "office", "commercial", "godown", "warehouse")):
        return "commercial"
    if any(w in t for w in ("car", "bike", "scooter", "vehicle", "suv", "hatchback", "sedan", "motorcycle")):
        return "vehicle"
    return "apartment"  # most common default


def _smart_defaults(screen: str, record_data: dict, provided: dict) -> None:
    """Auto-derive fields the user didn't speak, from context. Mutates record_data."""
    if screen == "properties" and "type" not in record_data:
        # Infer from the name ("my Powai flat" -> apartment) or default to apartment
        record_data["type"] = _infer_property_type(provided.get("name") or provided.get("address") or "")
    if screen == "properties" and "ownership_type" not in record_data:
        record_data["ownership_type"] = "owned"
    if screen == "bills" and "bill_type" not in record_data:
        # Infer bill type from provider name (Tata Power -> electricity etc.)
        provider = (record_data.get("provider") or "").lower()
        hints = {
            "electricity": ["electric", "power", "bescom", "mseb", "torrent", "adani"],
            "mobile": ["airtel", "jio", "vodafone", "vi ", "bsnl", "mobile"],
            "internet": ["broadband", "fiber", "act ", "hathway", "wifi", "internet"],
            "gas": ["gas", "indane", "hp gas", "png"],
            "water": ["water", "municipal"],
            "credit_card": ["card", "hdfc", "icici", "sbi card", "axis"],
        }
        for btype, words in hints.items():
            if any(h in provider for h in hints[btype]):
                record_data["bill_type"] = btype
                break
        else:
            record_data["bill_type"] = "other"
    if screen == "obligations" and "category" not in record_data:
        name = (record_data.get("name") or "").lower()
        if any(w in name for w in ("loan", "emi")):
            record_data["category"] = "loan"
        elif "rent" in name:
            record_data["category"] = "rent"
        elif any(w in name for w in ("netflix", "spotify", "subscription", "prime")):
            record_data["category"] = "subscription"
        else:
            record_data["category"] = "other"


def _do_create(screen: str, provided: dict, db: Session, user: User) -> dict:
    """Core create logic shared by GET and POST endpoints."""
    screen = screen.lower().strip()
    if screen not in SCREEN_FORM_FIELDS:
        return {"error": f"Cannot create items on screen '{screen}'. Available: {list(SCREEN_FORM_FIELDS.keys())}"}

    config = SCREEN_FORM_FIELDS[screen]
    model = config["model"]
    field_map = config["fields"]
    defaults = config.get("defaults", {})

    record_data = {}
    for voice_field, db_col in field_map.items():
        val = provided.get(voice_field) or provided.get(db_col)
        if val is not None and val != "":
            col_type = model.__table__.columns[db_col].type
            if hasattr(col_type, 'python_type'):
                try:
                    if col_type.python_type == float and isinstance(val, (str, int)):
                        val = float(str(val).replace(",", "").replace("₹", "").strip())
                    elif col_type.python_type == int and isinstance(val, str):
                        val = int(val)
                except Exception:
                    pass
            # Date columns: accept natural language ("tomorrow", "15th of next month", "25th August")
            if hasattr(col_type, 'python_type') and col_type.python_type == date and isinstance(val, str):
                parsed, derr = resolve_single_date(val)
                if parsed:
                    val = parsed
                else:
                    return {"error": f"Couldn't understand the date '{val}' for '{voice_field}'. {derr}", "needs_date": True}
            record_data[db_col] = val

    # Auto-derive unstated fields from context (property type, bill type, ...)
    _smart_defaults(screen, record_data, provided)

    if not record_data:
        return {"error": f"No fields provided. Expected one of: {list(field_map.keys())}"}

    # Auto-derive maintenance type from title if missing
    if screen == "maintenance" and "type" not in record_data:
        title_lower = (record_data.get("title", "") or "").lower()
        if "ac" in title_lower:
            record_data["type"] = "ac_service"
        elif "plumb" in title_lower:
            record_data["type"] = "plumbing"
        elif "electric" in title_lower:
            record_data["type"] = "electrical"
        elif "clean" in title_lower:
            record_data["type"] = "cleaning"
        elif "paint" in title_lower:
            record_data["type"] = "painting"
        elif "pest" in title_lower:
            record_data["type"] = "pest_control"
        elif "water" in title_lower or "tank" in title_lower:
            record_data["type"] = "water_tank"
        elif "garden" in title_lower or "landscape" in title_lower:
            record_data["type"] = "gardening"
        else:
            record_data["type"] = "general"

    for k, v in defaults.items():
        if k not in record_data:
            record_data[k] = v

    # Pre-insert validation: with auto-derivation, anything still missing genuinely
    # needs the user. Ask for ONLY the missing fields, conversationally.
    required = REQUIRED_FIELDS.get(screen, [])
    missing = [f for f in required if not record_data.get(f)]
    if missing:
        return {
            "error": f"I can add the {screen[:-1] if screen != 'health' else 'health profile'} — I just need a bit more info: {', '.join(missing)}. "
                     f"Please tell me the {missing[0]} and I'll create it.",
            "missing_required_fields": missing,
            "required_fields_for_screen": required,
        }

    try:
        record = model(user_id=user.id, **record_data)
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as e:
        db.rollback()
        return {"error": f"Failed to create record: {str(e)}"}

    serialized = _serialize(record)

    push_navigation(config["nav_screen"], "navigate", {
        "screen": config["nav_screen"],
        "type": "table" if screen != "health" else "cards",
        "created": True,
        "item": serialized,
        "message": f"Created new {screen[:-1]}: {_describe_item(screen, serialized)}",
    })

    return {
        "screen": screen,
        "action": "created",
        "status": "success",
        "item": serialized,
        "message": f"Successfully created a new {screen[:-1]}: {_describe_item(screen, serialized)}",
        # Proactive hint so the agent knows the contract for the NEXT create on this screen
        "required_fields_note": f"For future creates on '{screen}', always include: {REQUIRED_FIELDS.get(screen, [])}",
    }


@router.get("/create")
async def create_item_get(
    request: StarletteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(_check_auth),
):
    """Create a new item via query params — Dograh HTTP tool compatible."""
    params = dict(request.query_params)
    screen = params.pop("screen", None)
    if not screen:
        return {"error": "Missing required param: screen"}
    return _do_create(screen, params, db, user)




@router.get("/update")
def update_item(
    request: StarletteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(_check_auth),
):
    """Update an existing item — find by name/match, then update fields."""
    params = dict(request.query_params)
    screen = params.pop("screen", None)
    item_id = params.pop("id", None)
    match = params.pop("match", None)  # text to match against item fields
    
    if not screen:
        return {"error": "Missing required param: screen"}
    screen = screen.lower().strip()
    if screen not in SCREEN_FORM_FIELDS:
        return {"error": f"Invalid screen: {screen}. Available: {list(SCREEN_FORM_FIELDS.keys())}"}
    
    config = SCREEN_FORM_FIELDS[screen]
    model = config["model"]
    field_map = config["fields"]
    
    # Find the record by ID or by text match
    query = db.query(model).filter(getattr(model, "user_id") == user.id)
    
    if item_id:
        record = query.filter(model.id == int(item_id)).first()
    elif match:
        # Search across all string fields
        records = query.all()
        record = None
        match_lower = match.lower()
        for r in records:
            serialized = _serialize(r)
            text = " ".join(str(v) for v in serialized.values() if v).lower()
            if match_lower in text:
                record = r
                break
        if not record:
            return {"error": f"No {screen[:-1]} found matching '{match}'"}
    else:
        return {"error": "Provide either id=<number> or match=<text> to find the record to update"}
    
    if not record:
        return {"error": f"{screen[:-1]} not found"}
    
    # Build update data from remaining params
    updates = {}
    for voice_field, db_col in field_map.items():
        val = params.get(voice_field) or params.get(db_col)
        if val is not None and val != "":
            col_type = model.__table__.columns[db_col].type
            if hasattr(col_type, 'python_type'):
                try:
                    if col_type.python_type == float and isinstance(val, (str, int)):
                        val = float(str(val).replace(",", "").replace("₹", "").strip())
                    elif col_type.python_type == int and isinstance(val, str):
                        val = int(val)
                except Exception:
                    pass
            if hasattr(col_type, 'python_type') and col_type.python_type == date and isinstance(val, str):
                parsed, derr = resolve_single_date(val)
                if parsed:
                    val = parsed
                else:
                    return {"error": f"Couldn't understand the date '{val}' for '{voice_field}'. {derr}", "needs_date": True}
            updates[db_col] = val
    
    # Special fields: status mapping per screen
    # maintenance: status=completed → date_completed=today, status=pending → date_completed=None
    # bills: status=paid → paid_date=today+status=paid, status=pending → paid_date=None+status=pending
    # obligations: status=paid → last_paid_date=today
    if "status" in params and params["status"]:
        status_val = params["status"].lower()
        from datetime import date as _date
        if screen == "maintenance":
            if status_val in ("completed", "done", "complete"):
                updates["date_completed"] = _date.today()
            elif status_val in ("pending", "open", "incomplete"):
                updates["date_completed"] = None
        elif screen == "bills":
            if status_val in ("paid", "completed"):
                updates["status"] = "paid"
                updates["paid_date"] = _date.today()
            elif status_val in ("pending", "unpaid", "open"):
                updates["status"] = "pending"
                updates["paid_date"] = None
        elif screen == "obligations":
            if status_val in ("paid", "completed"):
                updates["last_paid_date"] = _date.today()
        elif screen == "insurance":
            if status_val in ("lapsed", "expired"):
                updates["status"] = "lapsed"
            elif status_val in ("active", "renewed"):
                updates["status"] = "active"
        else:
            # Generic: set status if the column exists
            if hasattr(record, "status"):
                updates["status"] = params["status"]
    
    if not updates:
        return {"error": f"No update fields provided. Available: {list(field_map.keys())} + status"}
    
    # Apply updates
    for k, v in updates.items():
        if hasattr(record, k):
            setattr(record, k, v)
    
    try:
        db.commit()
        db.refresh(record)
    except Exception as e:
        db.rollback()
        return {"error": f"Failed to update: {str(e)}"}
    
    serialized = _serialize(record)
    
    push_navigation(config["nav_screen"], "navigate", {
        "screen": config["nav_screen"],
        "type": "table" if screen != "health" else "cards",
        "updated": True,
        "item": serialized,
        "message": f"Updated {screen[:-1]}: {_describe_item(screen, serialized)}",
    })
    
    return {
        "screen": screen,
        "action": "updated",
        "status": "success",
        "item": serialized,
        "message": f"Successfully updated the {screen[:-1]}: {_describe_item(screen, serialized)}",
    }


@router.get("/action")
def do_action(
    request: StarletteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(_check_auth),
):
    """Perform an action on an item — pay bill, mark obligation paid, delete, etc."""
    params = dict(request.query_params)
    screen = params.pop("screen", None)
    item_id = params.pop("id", None)
    match = params.pop("match", None)
    action = params.pop("action", None)
    
    if not screen or not action:
        return {"error": "Missing required params: screen and action (e.g. screen=bills&action=pay)"}
    
    screen = screen.lower().strip()
    
    # Find the record
    if screen not in SCREEN_FORM_FIELDS:
        return {"error": f"Invalid screen: {screen}"}
    
    model = SCREEN_FORM_FIELDS[screen]["model"]
    query = db.query(model).filter(getattr(model, "user_id") == user.id)
    
    if item_id:
        record = query.filter(model.id == int(item_id)).first()
    elif match:
        records = query.all()
        record = None
        match_lower = match.lower()
        for r in records:
            serialized = _serialize(r)
            text = " ".join(str(v) for v in serialized.values() if v).lower()
            if match_lower in text:
                record = r
                break
    else:
        return {"error": "Provide id=<number> or match=<text> to find the record"}
    
    if not record:
        return {"error": f"Record not found in {screen}"}
    
    # Execute action
    from datetime import date as _date
    
    if action == "pay" and screen == "bills":
        record.status = "paid"
        record.paid_date = _date.today()
        record.paid_amount = record.amount
        msg = f"Bill '{record.provider}' marked as paid"
    elif action == "mark_paid" and screen == "obligations":
        record.last_paid_date = _date.today()
        msg = f"Obligation '{record.name}' marked as paid"
    elif action == "delete":
        item_desc = match or item_id or ""
        db.delete(record)
        db.commit()
        push_navigation(screen, "navigate", {"screen": screen, "deleted": True, "message": f"Deleted {screen[:-1]}: {item_desc}"})
        return {"screen": screen, "action": "deleted", "status": "success", "message": f"Successfully deleted {screen[:-1]}: {item_desc}"}
    elif action == "complete" and screen == "maintenance":
        record.date_completed = _date.today()
        msg = f"Maintenance '{record.title}' marked as completed"
    else:
        return {"error": f"Unknown action '{action}' for screen '{screen}'. Available: pay, mark_paid, complete, delete"}
    
    try:
        db.commit()
        db.refresh(record)
    except Exception as e:
        db.rollback()
        return {"error": f"Failed: {str(e)}"}
    
    serialized = _serialize(record)
    push_navigation(SCREEN_FORM_FIELDS[screen]["nav_screen"], "navigate", {
        "screen": SCREEN_FORM_FIELDS[screen]["nav_screen"],
        "action_done": True,
        "item": serialized,
        "message": msg,
    })
    
    return {
        "screen": screen,
        "action": action,
        "status": "success",
        "item": serialized,
        "message": msg,
    }



def _describe_item(screen: str, item: dict) -> str:
    """Generate a human-readable description of the created item"""
    if screen == "bills":
        return f"{item.get('bill_type','')} bill from {item.get('provider','')} for ₹{item.get('amount',0)} due {item.get('due_date','')}"
    elif screen == "obligations":
        return f"{item.get('name','')} — ₹{item.get('amount',0)} {item.get('frequency','')}"
    elif screen == "insurance":
        return f"{item.get('policy_type','')} policy from {item.get('provider','')} — ₹{item.get('premium_amount',0)}/yr"
    elif screen == "properties":
        return f"{item.get('name','')} ({item.get('type','')}) at {item.get('address','')}"
    elif screen == "maintenance":
        return f"{item.get('title','')} — {item.get('type','')} for ₹{item.get('cost',0)}"
    elif screen == "health":
        return f"Health profile for {item.get('member_name','')} ({item.get('member_relationship','')})"
    elif screen == "documents":
        return f"{item.get('name','')} — {item.get('category','')}"
    return str(item)


@router.get("/export")
def export_action(action: str = Query(...), db: Session = Depends(get_db), user: User = Depends(_check_auth)):
    """Trigger an export action — returns data for export"""
    today = date.today()
    bills = db.query(Bill).filter(Bill.user_id == user.id).all()
    
    if action == "export_csv" or action == "export_pdf":
        return {
            "action": action,
            "status": "ready",
            "format": "csv" if "csv" in action else "pdf",
            "data": [_serialize(b) for b in bills],
            "message": f"Exported {len(bills)} bills. The export file is ready for download.",
        }
    elif action == "print":
        return {"action": "print", "status": "ready", "message": "Print dialog opened."}
    return {"error": f"Unknown action: {action}"}


def _serialize(obj):
    """Convert SQLAlchemy model to dict, handling common fields"""
    result = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if val is not None:
            if hasattr(val, "isoformat"):
                result[col.name] = val.isoformat()
            elif isinstance(val, (int, float, str, bool)):
                result[col.name] = val
            else:
                result[col.name] = str(val)
        else:
            result[col.name] = None
    return result