import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.album import Album, AlbumStatus
from app.models.image import Image as ImageModel, ImageStatus
from app.models.user import User
from app.routers.auth import get_current_user, require_supervisor
from app.schemas.image import ImageResponse, QuarantineResponse
from app.services import image_processor, steg_analyzer

router = APIRouter(tags=["Images"])
settings = get_settings()

_MAX_BYTES = settings.max_file_size_bytes


# ── Upload image ──────────────────────────────────────────────────────────
@router.post(
    "/albums/{album_id}/images",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload image to an approved album (RF03)",
)
async def upload_image(
    album_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Verificar que el álbum existe y está aprobado
    album = db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    if album.status != AlbumStatus.approved:
        raise HTTPException(status_code=403, detail="Album is not approved for uploads")
    if album.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't own this album")

    # 2. Leer archivo y validar tamaño
    raw_bytes = await file.read()
    if len(raw_bytes) > _MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.max_file_size_mb} MB",
        )

    # 3. Validar MIME + strip EXIF + re-encode
    try:
        processed_bytes, mime_type, extension = image_processor.validate_and_process_image(
            raw_bytes, file.filename or "upload"
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # 4. Análisis de esteganografía
    steg_result = steg_analyzer.analyze_image(processed_bytes, mime_type)

    # 5. Determinar estado según resultado del análisis
    img_status = (
        ImageStatus.quarantined
        if steg_result.get("is_suspicious")
        else ImageStatus.clean
    )

    # 6. Guardar archivo procesado en disco
    stored_filename = image_processor.generate_stored_filename(extension)
    file_path = image_processor.save_file(processed_bytes, stored_filename)

    # 7. Persistir en BD
    image_record = ImageModel(
        original_filename=file.filename or "upload",
        stored_filename=stored_filename,
        file_path=file_path,
        mime_type=mime_type,
        file_size=len(processed_bytes),
        status=img_status,
        steg_result=steg_result,
        album_id=album_id,
        owner_id=current_user.id,
    )
    db.add(image_record)
    db.commit()
    db.refresh(image_record)
    return image_record


# ── List images in album (public) ─────────────────────────────────────────
@router.get(
    "/albums/{album_id}/images",
    response_model=list[ImageResponse],
    summary="List approved/clean images in an album (RF05)",
)
def list_album_images(album_id: int, db: Session = Depends(get_db)):
    album = db.get(Album, album_id)
    if not album or album.status != AlbumStatus.approved:
        raise HTTPException(status_code=404, detail="Album not found or not public")
    return (
        db.query(ImageModel)
        .filter(
            ImageModel.album_id == album_id,
            ImageModel.status.in_([ImageStatus.clean, ImageStatus.approved_manual]),
        )
        .order_by(ImageModel.created_at.desc())
        .all()
    )


# ── Serve image file ──────────────────────────────────────────────────────
@router.get(
    "/images/{stored_filename}",
    summary="Serve an image file (RF05)",
    response_class=FileResponse,
)
def serve_image(stored_filename: str, db: Session = Depends(get_db)):
    # Prevenir path traversal
    if "/" in stored_filename or "\\" in stored_filename or ".." in stored_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    record = db.query(ImageModel).filter(
        ImageModel.stored_filename == stored_filename
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Image not found")
    if record.status not in (ImageStatus.clean, ImageStatus.approved_manual):
        raise HTTPException(status_code=403, detail="Image not available")

    if not os.path.exists(record.file_path):
        raise HTTPException(status_code=404, detail="Image file missing")

    return FileResponse(
        record.file_path,
        media_type=record.mime_type,
        headers={"X-Content-Type-Options": "nosniff"},
    )


# ── Quarantine endpoints (Supervisor) ─────────────────────────────────────
@router.get(
    "/quarantine",
    response_model=list[QuarantineResponse],
    summary="List quarantined images (supervisor — RF04)",
)
def list_quarantine(
    _: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    return (
        db.query(ImageModel)
        .filter(ImageModel.status == ImageStatus.quarantined)
        .order_by(ImageModel.created_at.asc())
        .all()
    )


@router.patch(
    "/quarantine/{image_id}/approve",
    response_model=QuarantineResponse,
    summary="Approve quarantined image — make it public (RF04)",
)
def approve_quarantined(
    image_id: int,
    reviewer: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    img = db.get(ImageModel, image_id)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    if img.status != ImageStatus.quarantined:
        raise HTTPException(status_code=409, detail="Image is not in quarantine")

    img.status = ImageStatus.approved_manual
    img.reviewer_id = reviewer.id
    img.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(img)
    return img


@router.patch(
    "/quarantine/{image_id}/reject",
    response_model=QuarantineResponse,
    summary="Reject quarantined image — delete permanently (RF04)",
)
def reject_quarantined(
    image_id: int,
    reviewer: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    img = db.get(ImageModel, image_id)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    if img.status != ImageStatus.quarantined:
        raise HTTPException(status_code=409, detail="Image is not in quarantine")

    # Eliminar archivo del disco
    if os.path.exists(img.file_path):
        os.remove(img.file_path)

    img.status = ImageStatus.rejected
    img.reviewer_id = reviewer.id
    img.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(img)
    return img
