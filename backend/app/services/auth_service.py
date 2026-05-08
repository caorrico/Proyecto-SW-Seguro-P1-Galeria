from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Anti-enumeration setup: dummy hash for response timing equivalence
dummy_hash = pwd_context.hash("dummy_password_for_timing")
# Token blocklist (for demonstration purposes, in-memory)
# In production, use Redis or DB with TTL.
token_blocklist = set()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        return pwd_context.verify(password, stored_hash)
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    # Refresh token typically has a longer lifespan, e.g., 7 days
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalido o expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token in token_blocklist:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "access":
            raise credentials_exception
        user_id = payload.get("sub")
        token_version = payload.get("token_version")
        if user_id is None or token_version is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc
        
    user = db.get(User, int(user_id))
    if user is None:
        raise credentials_exception
        
    if user.status == "BLOCKED":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta bloqueada. Contacte al administrador.")
        
    if user.token_version != token_version:
        raise credentials_exception
        
    return user


def require_supervisor_or_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {"supervisor", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes.")
    return current_user
