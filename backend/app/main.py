import os
import logging
from contextlib import asynccontextmanager

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.config import get_settings
from app.database import init_db
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.rate_limiter import limiter
from app.routers import auth as auth_router

# ── Placeholder imports para P2 (se agregarán via PR) ───────────────────
# from app.routers import albums as albums_router
# from app.routers import images as images_router
# from app.routers import quarantine as quarantine_router

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting SecureFrame Gallery API...")
    init_db()
    os.makedirs(settings.upload_dir, exist_ok=True)
    _seed_supervisor()
    logger.info("Database initialized and uploads directory ready.")
    yield
    # Shutdown
    logger.info("Shutting down SecureFrame Gallery API.")


def _seed_supervisor() -> None:
    """Crea el usuario supervisor por defecto si no existe."""
    from app.database import SessionLocal
    from app.services import auth_service
    from app.models.user import UserRole

    db = SessionLocal()
    try:
        existing = auth_service.get_user_by_username(db, "supervisor")
        if not existing:
            user = auth_service.create_user(
                db,
                username="supervisor",
                email="supervisor@secureframe.local",
                password="Sup3rv!s0r#2026",
            )
            user.role = UserRole.supervisor
            db.commit()
            logger.info("Default supervisor user created.")
    finally:
        db.close()


# ── App factory ───────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Secure image gallery with steganography detection. "
        "Built for Secure Software Development course."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── Rate limiter ──────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Security Headers ──────────────────────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)


# ── Global error handler (no exponer stack traces) ────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
    )


# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(auth_router.router, prefix="/api")

# P2 agregará estos via PR:
# app.include_router(albums_router.router, prefix="/api")
# app.include_router(images_router.router, prefix="/api")
# app.include_router(quarantine_router.router, prefix="/api")


# ── Health check ──────────────────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
def health_check():
    return {"status": "ok", "version": settings.app_version}
