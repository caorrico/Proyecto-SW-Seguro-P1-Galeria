from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserLogin, UserResponse
from app.services.auth_service import create_access_token, create_refresh_token, get_current_user, hash_password, verify_password, oauth2_scheme, dummy_hash, token_blocklist
from app.models.refresh_token import RefreshToken

logger = logging.getLogger(__name__)
from app.middleware.rate_limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(or_(User.username == payload.username, User.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuario o email ya registrado.")
    user = User(
        username=payload.username.strip(),
        email=str(payload.email).lower(),
        hashed_password=hash_password(payload.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, response: Response, payload: UserLogin, db: Session = Depends(get_db)):
    login_id = payload.username.strip()
    user = db.query(User).filter(or_(User.username == login_id, User.email == login_id.lower())).first()
    
    # Anti-enumeration via timing equivalence
    if not user:
        verify_password(payload.password, dummy_hash)
        logger.warning(f"Failed login attempt for non-existent user: {payload.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas.")

    if user.status == "BLOCKED":
        logger.warning(f"Login attempt on blocked account: {user.username}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta bloqueada. Contacte al administrador.")

    if user.locked_until and user.locked_until > datetime.utcnow():
        logger.warning(f"Login attempt on locked account: {user.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Demasiados intentos. Intente más tarde.")

    if not verify_password(payload.password, user.hashed_password):
        user.failed_login_count += 1
        if user.failed_login_count >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            logger.warning(f"Account locked due to multiple failed logins: {user.username}")
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas.")
        
    # Successful login
    user.failed_login_count = 0
    user.locked_until = None
    db.commit()
    
    
    token_payload = {"sub": str(user.id), "role": user.role, "token_version": user.token_version}
    access_token = create_access_token(token_payload)
    refresh_token, jti = create_refresh_token(token_payload)
    
    # Persistir JTI en DB
    db_session = RefreshToken(
        jti=jti,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(db_session)
    db.commit()

    response.set_cookie(
        key="secureframe_refresh",
        value=refresh_token,
        httponly=True,
        secure=False, 
        samesite="lax",
        max_age=7 * 24 * 60 * 60 # 7 days
    )
    
    logger.info(f"User logged in successfully: {user.username} (JTI: {jti})")
    return Token(access_token=access_token, user=user)

@router.post("/refresh", response_model=Token)
def refresh_token(response: Response, secureframe_refresh: str | None = Cookie(None), db: Session = Depends(get_db)):
    if not secureframe_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No se encontró el token de refresco.")
        
    try:
        from jose import jwt, JWTError
        from app.config import settings
        
        payload = jwt.decode(secureframe_refresh, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tipo de token inválido.")
            
        user_id = payload.get("sub")
        token_version = payload.get("token_version")
        jti = payload.get("jti")

        if user_id is None or token_version is None or jti is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Contenido del token inválido.")
            
        user = db.get(User, int(user_id))
        if user is None or user.status == "BLOCKED" or user.token_version != token_version:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o usuario bloqueado.")

        # VERIFICACIÓN DE REUTILIZACIÓN (Replay Attack Prevention)
        stored_session = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        if not stored_session:
            # ¡REUTILIZACIÓN DETECTADA! El token es válido pero el JTI ya no está en la DB.
            # Revocamos TODA la familia de tokens por seguridad.
            logger.warning(f"TOKEN REUSE DETECTED for user {user.username}. Invalidating all sessions.")
            user.token_version += 1
            db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete()
            db.commit()
            response.delete_cookie("secureframe_refresh")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Se detectó reutilización de token. Inicia sesión nuevamente.")

        # Rotar token: borrar viejo JTI, crear uno nuevo
        db.delete(stored_session)
        db.commit()

        token_payload = {"sub": str(user.id), "role": user.role, "token_version": user.token_version}
        new_access_token = create_access_token(token_payload)
        new_refresh_token, new_jti = create_refresh_token(token_payload)
        
        # Guardar nuevo JTI
        new_db_session = RefreshToken(
            jti=new_jti,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(new_db_session)
        db.commit()

        response.set_cookie(
            key="secureframe_refresh",
            value=new_refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=7 * 24 * 60 * 60
        )
        return Token(access_token=new_access_token, user=user)
        
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de refresco inválido.")

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(response: Response, token: str = Depends(oauth2_scheme)):
    token_blocklist.add(token)
    response.delete_cookie("secureframe_refresh")
    return {"detail": "Sesión cerrada exitosamente."}

@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
