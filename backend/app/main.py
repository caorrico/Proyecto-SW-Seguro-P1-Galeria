import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import Base, engine, SessionLocal
from app.middleware.rate_limiter import limiter
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.models import Album, Image, User
from app.models.user import User as UserModel
from app.routers import albums, auth, images
from app.services.auth_service import hash_password

logger = logging.getLogger(__name__)


def _init_db(max_retries: int = 5, delay: int = 3):
    """Create tables and seed admin user, with retries for slow DB starts."""
    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created/verified.")

            # Auto-seed admin user if it doesn't exist
            db = SessionLocal()
            try:
                admin = db.query(UserModel).filter(UserModel.username == "admin").first()
                if not admin:
                    from datetime import datetime
                    admin = UserModel(
                        username="admin",
                        email="admin@secureframe.com",
                        hashed_password=hash_password("admin123"),
                        role="admin",
                        status="ACTIVE",
                        token_version=1,
                        created_at=datetime.utcnow(),
                    )
                    db.add(admin)
                    db.commit()
                    logger.info("Admin user seeded (admin / admin123).")
                else:
                    logger.info("Admin user already exists.")
            finally:
                db.close()
            return
        except Exception as exc:
            logger.warning(f"DB init attempt {attempt}/{max_retries} failed: {exc}")
            if attempt < max_retries:
                time.sleep(delay)
            else:
                logger.error("Could not connect to database after retries. Starting without DB init.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(albums.router, prefix="/api")
app.include_router(images.router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.app_name}

