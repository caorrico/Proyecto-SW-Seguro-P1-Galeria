import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.image import Image
from app.models.user import User
from app.schemas.image import ImageResponse
from app.services.auth_service import require_supervisor
from app.services.storage_service import storage_service

router = APIRouter(prefix="/quarantine", tags=["quarantine"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[ImageResponse])
def list_quarantine(
    _: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    return (
        db.query(Image)
        .filter(Image.status == "SUSPICIOUS")
        .order_by(Image.created_at.desc())
        .all()
    )


@router.patch("/{image_id}/approve", response_model=ImageResponse)
def approve_quarantine_image(
    image_id: int,
    _: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada.")

    if not storage_service.move_object("quarantine", "public", image.stored_path):
        logger.warning("No se pudo mover el archivo fisico %s, procediendo solo con DB.", image.stored_path)

    image.status = "APPROVED_MANUAL"
    db.commit()
    db.refresh(image)
    return image


@router.patch("/{image_id}/reject", response_model=ImageResponse)
def reject_quarantine_image(
    image_id: int,
    _: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada.")

    if not storage_service.move_object("quarantine", "evidence", image.stored_path):
        logger.warning("No se pudo mover el archivo fisico %s a evidencia, procediendo solo con DB.", image.stored_path)

    image.status = "REJECTED"
    db.commit()
    db.refresh(image)
    return image
