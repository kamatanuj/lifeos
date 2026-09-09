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