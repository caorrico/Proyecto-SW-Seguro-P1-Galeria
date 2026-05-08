import enum
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ImageStatus(str, enum.Enum):
    clean           = "CLEAN"
    quarantined     = "QUARANTINED"
    approved_manual = "APPROVED_MANUAL"
    rejected        = "REJECTED"


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename:   Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_path:         Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type:         Mapped[str] = mapped_column(String(50),  nullable=False)
    file_size:         Mapped[int] = mapped_column(Integer,      nullable=False)  # bytes

    status: Mapped[ImageStatus] = mapped_column(
        SAEnum(ImageStatus), default=ImageStatus.clean, nullable=False
    )

    # Resultado del análisis esteganográfico (guardado como JSON)
    steg_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    album_id: Mapped[int] = mapped_column(
        ForeignKey("albums.id", ondelete="CASCADE"), nullable=False
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    album    = relationship("Album", back_populates="images")
    owner    = relationship("User", foreign_keys=[owner_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    def __repr__(self) -> str:
        return (
            f"<Image id={self.id} file={self.stored_filename!r} "
            f"status={self.status} album={self.album_id}>"
        )
