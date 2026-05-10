import enum
from datetime import datetime

# pyrefly: ignore [missing-import]
from sqlalchemy import DateTime, String, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    visitor    = "visitor"
    user       = "user"
    supervisor = "supervisor"
    admin      = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.user, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Security fields
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False) # ACTIVE, BLOCKED
    token_version: Mapped[int] = mapped_column(default=1, nullable=False)
    failed_login_count: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    albums = relationship("Album", back_populates="owner", foreign_keys="Album.user_id")
    reviewed_albums = relationship("Album", foreign_keys="Album.reviewed_by", overlaps="reviewer")
