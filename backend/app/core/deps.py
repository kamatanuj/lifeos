"""Dependencies — get current user from JWT or API key"""
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# Static API key for external integrations (Dograh tools)
API_KEY = "lifeos_dograh_2026"


def get_current_user(
    token: str = Depends(oauth2_scheme),
    x_api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User:
    # Check API key first (for Dograh tools)
    if x_api_key and x_api_key == API_KEY:
        user = db.query(User).first()
        if user:
            return user
        raise HTTPException(status_code=401, detail="No users in database")
    
    # Then check JWT token
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user