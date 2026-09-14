"""Documents router — CRUD + summary (file storage as local path for now)"""
import os
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.models import Document
from app.schemas import DocumentResponse

router = APIRouter(prefix="/api/documents", tags=["documents"])
UPLOAD_DIR = "/var/www/lifeos-docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("")
def list_documents(category: str = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Document).filter(Document.user_id == user.id)
    if category:
        q = q.filter(Document.category == category)
    return q.order_by(Document.uploaded_at.desc()).all()


@router.get("/summary")
def document_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    docs = db.query(Document).filter(Document.user_id == user.id).all()
    total = len(docs)
    storage_used = sum(d.file_size or 0 for d in docs)
    categories = len(set(d.category for d in docs))
    expiring_soon = sum(1 for d in docs if d.expiry_date and d.expiry_date <= date.today().replace(day=date.today().day) and d.expiry_date.month == date.today().month)
    return {"total": total, "storage_used": storage_used, "categories": categories, "expiring_soon": expiring_soon}


@router.post("", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    name: str = Form(...),
    category: str = Form(...),
    linked_type: str = Form(None),
    linked_id: int = Form(None),
    notes: str = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Save file
    file_path = os.path.join(UPLOAD_DIR, f"{user.id}_{file.filename}")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    doc = Document(
        user_id=user.id,
        name=name,
        category=category,
        linked_type=linked_type,
        linked_id=linked_id,
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        mime_type=file.content_type,
        notes=notes,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/{did}", response_model=DocumentResponse)
def get_document(did: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == did, Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{did}/download")
def download_document(did: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from fastapi.responses import FileResponse
    doc = db.query(Document).filter(Document.id == did, Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(doc.file_path, filename=doc.name)


@router.put("/{did}", response_model=DocumentResponse)
def update_document(did: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Update document metadata (name, category, expiry_date, notes) — file itself unchanged."""
    doc = db.query(Document).filter(Document.id == did, Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    for k, v in payload.items():
        if hasattr(Document, k) and k not in ("id", "user_id", "file_path", "file_size", "created_at"):
            setattr(doc, k, v)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{did}")
def delete_document(did: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == did, Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
    return {"deleted": True}


@router.post("/{did}/summarize")
def summarize_document(did: int, force: bool = False, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Extract text (OCR fallback), run glm-5.3-flash analysis, store summary + payment findings.
    Caches: if the file content hash is unchanged and a summary exists, return it without re-running the LLM.
    Use ?force=true (or the Re-analyze button) to regenerate."""
    import hashlib
    from datetime import datetime, timezone
    from app.services.doc_intelligence import extract_text, analyze

    doc = db.query(Document).filter(Document.id == did, Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=400, detail="File not found on disk")

    # content hash for cache invalidation
    with open(doc.file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    if not force and doc.content_hash == file_hash and doc.summary_text and doc.processed_at:
        return {
            "id": doc.id,
            "summary": doc.summary_text,
            "payments": doc.extracted_payments,
            "extraction_method": doc.extraction_method,
            "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
            "cached": True,
        }

    try:
        text, method = extract_text(doc.file_path, doc.mime_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {e}")

    if len(text.strip()) < 30:
        raise HTTPException(status_code=422, detail="Could not extract readable text from this document (unsupported type or unreadable scan)")

    try:
        result = analyze(text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {e}")

    doc.summary_text = result["summary"]
    doc.extracted_payments = result["payments"]
    if result.get("expiry_date") and not doc.expiry_date:
        try:
            from datetime import date as _date
            y, m, d = (int(x) for x in result["expiry_date"].split("-"))
            doc.expiry_date = _date(y, m, d)
        except (ValueError, TypeError):
            pass
    doc.extraction_method = method
    doc.processed_at = datetime.now(timezone.utc)
    doc.content_hash = file_hash
    doc.extracted_text = text
    db.commit()
    db.refresh(doc)
    return {
        "id": doc.id,
        "summary": doc.summary_text,
        "payments": doc.extracted_payments,
        "extraction_method": doc.extraction_method,
        "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
    }


@router.post("/{did}/create-bills")
def create_bills_from_document(did: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Create Bill rows from user-approved payment items. payload: {"payments": [{provider, amount, due_date, frequency, notes?}]}"""
    from app.models import Bill
    from app.schemas import BillCreate

    doc = db.query(Document).filter(Document.id == did, Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    items = payload.get("payments") or []
    if not items:
        raise HTTPException(status_code=422, detail="No payments selected")

    created = []
    from datetime import datetime as _dt, date as _date
    for p in items:
        try:
            amount = float(p.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0.0
        if amount <= 0:
            continue
        dd = p.get("due_date")
        if isinstance(dd, str) and len(dd) == 10:
            try:
                y, m, d = (int(x) for x in dd.split("-"))
                dd = _date(y, m, d)
            except (ValueError, TypeError):
                dd = None
        else:
            dd = None
        freq = (p.get("frequency") or "one_time").lower()
        if freq not in ("one_time", "monthly", "quarterly", "half_yearly", "yearly"):
            freq = "one_time"
        # due date is required by the Bill model; default to today + 30 days when missing
        if dd is None:
            import datetime as _datetime
            dd = _date.today() + _datetime.timedelta(days=30)
        bill_type = (p.get("bill_type") or "other").lower()[:50]
        provider = (p.get("provider") or "Unknown")[:255]
        notes = p.get("notes") or f"From document: {doc.name} (doc #{doc.id})"
        bill = Bill(
            user_id=user.id,
            bill_type=bill_type if bill_type else "other",
            provider=provider,
            amount=amount,
            due_date=dd,
            frequency=freq,
            notes=notes[:1000],
            status="pending",
        )
        db.add(bill)
        db.flush()
        created.append({"id": bill.id, "provider": bill.provider, "amount": bill.amount, "due_date": bill.due_date.isoformat(), "frequency": bill.frequency})
    db.commit()
    return {"created": created, "count": len(created)}

@router.get("/{did}/chat")
def get_chat(did: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Chat history for a document."""
    from app.models import DocumentChat
    doc = db.query(Document).filter(Document.id == did, Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    msgs = db.query(DocumentChat).filter(DocumentChat.document_id == did, DocumentChat.user_id == user.id).order_by(DocumentChat.created_at).all()
    return [{"role": m.role, "message": m.message, "created_at": m.created_at.isoformat() if m.created_at else None} for m in msgs]


@router.post("/{did}/chat")
def chat_with_document(did: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Ask a question about the document; grounded in the stored extracted text."""
    from app.models import DocumentChat
    from app.services.doc_intelligence import chat_answer

    doc = db.query(Document).filter(Document.id == did, Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.extracted_text or not doc.extracted_text.strip():
        raise HTTPException(status_code=400, detail="Run Summary first so the document text is extracted")

    question = (payload.get("question") or "").strip()
    if not question:
        raise HTTPException(status_code=422, detail="Empty question")

    history = db.query(DocumentChat).filter(DocumentChat.document_id == did, DocumentChat.user_id == user.id).order_by(DocumentChat.created_at).all()
    hist = [{"role": m.role, "content": m.message} for m in history]
    try:
        answer = chat_answer(doc.extracted_text, hist, question)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI chat failed: {e}")

    q = DocumentChat(document_id=did, user_id=user.id, role="user", message=question)
    a = DocumentChat(document_id=did, user_id=user.id, role="assistant", message=answer)
    db.add_all([q, a])
    db.commit()
    return {"question": question, "answer": answer}
