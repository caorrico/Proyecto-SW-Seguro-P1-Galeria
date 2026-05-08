from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.services import auth_service
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
_bearer = HTTPBearer(auto_error=False)

# ── Mensajes genéricos — previenen enumeración de usuarios ───────────────
_MSG_INVALID_CREDENTIALS = "Invalid username or password"
_MSG_USER_EXISTS         = "Registration failed"   # no revelar si user/email existe


# ── Dependency: usuario actual desde JWT ──────────────────────────────────
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise credentials_exception
    try:
        payload = auth_service.decode_token(credentials.credentials)
        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = auth_service.get_user_by_id(db, int(user_id))
    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_role(*roles: str):
    """Factory de dependencia que exige uno de los roles indicados."""
    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return _checker


require_user       = require_role("user", "supervisor")
require_supervisor = require_role("supervisor")


# ── Endpoints ────────────────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    # Comprobar duplicados — mensaje genérico para no revelar info
    existing = (
        auth_service.get_user_by_username(db, payload.username)
        or auth_service.get_user_by_email(db, payload.email)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_MSG_USER_EXISTS,
        )
    user = auth_service.create_user(
        db,
        username=payload.username,
        email=payload.email,
        password=payload.password,
    )
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive JWT",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, payload.username, payload.password)
    if not user:
        # Respuesta idéntica para credenciales incorrectas y usuario inexistente
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_MSG_INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_service.create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
def me(current_user: User = Depends(get_current_user)):
    return current_user
