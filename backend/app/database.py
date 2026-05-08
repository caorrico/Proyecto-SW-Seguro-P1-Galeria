from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

# SQLite necesita check_same_thread=False; en PostgreSQL se omite ese arg
connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.debug,       # Log SQL en modo debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base declarativa compartida por todos los modelos."""
    pass


def get_db():
    """
    Dependency de FastAPI para inyectar una sesión de BD
    y garantizar su cierre al finalizar el request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crea todas las tablas definidas en los modelos (si no existen)."""
    from app.models import user, album, image  # noqa: F401 – registrar modelos
    Base.metadata.create_all(bind=engine)
