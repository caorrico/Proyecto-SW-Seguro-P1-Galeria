from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.user import User, UserRole

settings = get_settings()

# ── Argon2id hasher ──────────────────────────────────────────────────────
# RFC recomendaciones: time_cost>=2, memory_cost>=64MB, parallelism>=1
_ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,   # 64 MB
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def hash_password(plain_password: str) -> str:
    """Retorna el hash Argon2id de la contraseña."""
    return _ph.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica la contraseña contra el hash.
    Retorna False en lugar de lanzar excepción — previene timing leaks parciales.
    """
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Detecta si el hash debe actualizarse (parámetros Argon2 cambiaron)."""
    return _ph.check_needs_rehash(hashed_password)


# ── JWT ──────────────────────────────────────────────────────────────────
def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decodifica y valida el JWT.
    Lanza JWTError si es inválido o expirado.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


# ── User queries ─────────────────────────────────────────────────────────
def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, username: str, email: str, password: str) -> User:
    user = User(
        username=username,
        email=email.lower(),
        hashed_password=hash_password(password),
        role=UserRole.user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    Busca al usuario por username o email y verifica la contraseña.
    Siempre ejecuta verify_password aunque el usuario no exista
    (dummy hash) para prevenir timing attacks de enumeración.
    """
    user = get_user_by_username(db, username) or get_user_by_email(db, username)

    # Dummy hash — se ejecuta incluso si el usuario no existe
    _DUMMY_HASH = "$argon2id$v=19$m=65536,t=2,p=2$dGVzdHNhbHQ$dGVzdGhhc2g"
    target_hash = user.hashed_password if user else _DUMMY_HASH

    if not verify_password(password, target_hash):
        return None
    if user and not user.is_active:
        return None
    return user
