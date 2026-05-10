from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, UploadFile, File
from sqlalchemy.orm import Session
from pathlib import Path
from uuid import uuid4

from app.database import get_db
from app.models.album import Album
from app.models.image import Image
from app.models.user import User
from app.middleware.rate_limiter import limiter
from app.schemas.album import AlbumCreate, AlbumResponse, AlbumReviewRequest, AlbumStatus
from app.schemas.image import ImageResponse
from app.services.auth_service import get_current_user, get_optional_current_user, require_supervisor
from app.services.storage_service import storage_service
from app.services.steg_analyzer import analyze_image
from app.services.image_processor import detect_mime_type, validate_and_process_image, check_eof_markers

router = APIRouter(prefix="/albums", tags=["albums"])
logger = logging.getLogger(__name__)


def ensure_pending(album: Album) -> None:
    if album.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se pueden revisar albumes en estado pending.",
        )


@router.post("/request", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
def request_album(payload: AlbumCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role in {"supervisor", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Los supervisores no pueden solicitar la creacion de albumes."
        )
    album = Album(
        title=payload.title,
        description=payload.description,
        privacy=payload.privacy,
        status="pending",
        user_id=current_user.id,
    )
    db.add(album)
    db.commit()
    db.refresh(album)
    return album


@router.get("/my", response_model=list[AlbumResponse])
def list_my_albums(
    status_filter: AlbumStatus | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Album).filter(Album.user_id == current_user.id)
    if status_filter:
        query = query.filter(Album.status == status_filter)
    return query.order_by(Album.created_at.desc()).all()


@router.get("/public", response_model=list[AlbumResponse])
def list_public_albums(db: Session = Depends(get_db)):
    return (
        db.query(Album)
        .filter(Album.status == "approved", Album.privacy == "public")
        .order_by(Album.created_at.desc())
        .all()
    )


@router.get("/pending", response_model=list[AlbumResponse])
def list_pending_albums(
    _: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    return (
        db.query(Album)
        .filter(Album.status == "pending")
        .order_by(Album.created_at.desc())
        .all()
    )


@router.patch("/{album_id}/review", response_model=AlbumResponse)
def review_album(
    album_id: int,
    payload: AlbumReviewRequest,
    reviewer: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    action = payload.action

    album = db.get(Album, album_id)
    if album is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album no encontrado.")
    
    ensure_pending(album)
    
    if action == "approve":
        album.status = "approved"
    else:
        album.status = "rejected"
        album.rejection_reason = payload.rejection_reason or "Rechazado por el supervisor."

    album.reviewed_by = reviewer.id
    album.reviewed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(album)

    # --- SEGURIDAD FÍSICA (MINIO) ---
    # Al aprobar/rechazar el álbum, procesamos físicamente todas sus imágenes
    for img in album.images:
        if action == "approve":
            # De cuarentena a público
            if storage_service.move_object("quarantine", "public", img.stored_path):
                img.status = "CLEAN"
        else:
            # De cuarentena a evidencia
            if storage_service.move_object("quarantine", "evidence", img.stored_path):
                img.status = "REJECTED"
    
    db.commit()
    return album


@router.post("/{album_id}/images", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def upload_album_image(
    request: Request,
    album_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    album = db.get(Album, album_id)
    if album is None or album.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album no encontrado.")
    
    if album.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo se pueden subir imagenes a albumes aprobados.",
        )

    # 1. Límite de Tamaño (DoS prevention)
    MAX_SIZE = 10 * 1024 * 1024 # 10MB
    file_content = await file.read()
    if len(file_content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande (máximo 10MB).")

    # 2. Detección de tipo real (Magic Bytes)
    mime = detect_mime_type(file_content)
    is_image = mime and mime.startswith("image/")
    if not is_image:
        raise HTTPException(status_code=422, detail="Solo se permiten imagenes validas.")

    # 3. Procesamiento y Sanitización
    processed_content = file_content
    safe_name = f"{uuid4().hex}_{Path(file.filename or 'archivo').name}"
    
    steg_result = {"result": "NOT_ANALYZED", "is_suspicious": False}

    if is_image:
        try:
            # Re-encoding y limpieza de EXIF
            processed_content, processed_mime, extension = validate_and_process_image(file_content, file.filename or "")
            mime = processed_mime
            # Actualizar nombre con la extensión correcta detectada
            safe_name = f"{uuid4().hex}{extension}"
            
            # Análisis de esteganografía LSB
            steg_result = analyze_image(processed_content, mime)
            
            # Análisis de datos ocultos al final del archivo (EOF)
            if check_eof_markers(file_content, mime):
                steg_result["result"] = "SUSPICIOUS"
                steg_result["is_suspicious"] = True
                steg_result["eof_alert"] = "DATA DETECTED AFTER EOF MARKER"
        except Exception as e:
            logger.warning("Image processing failed; upload sent to quarantine: %s", e)
            # Si falla el procesado de imagen, lo tratamos como sospechoso
            steg_result = {"result": "ERROR", "is_suspicious": True, "error": "IMAGE_PROCESSING_FAILED"}

    # 4. Subida a cuarentena
    stored_name = storage_service.upload_to_quarantine(
        file_data=processed_content,
        file_name=safe_name,
        content_type=mime or file.content_type or "application/octet-stream"
    )

    if not stored_name:
        raise HTTPException(status_code=500, detail="Error al subir el archivo a cuarentena.")

    # 5. Veredicto de estado
    final_status = "CLEAN"
    if steg_result.get("is_suspicious"):
        final_status = "SUSPICIOUS"
    elif not storage_service.move_object("quarantine", "public", stored_name):
        final_status = "SUSPICIOUS"
        steg_result["result"] = "SUSPICIOUS"
        steg_result["is_suspicious"] = True
        steg_result["storage_alert"] = "COULD_NOT_PROMOTE_TO_PUBLIC_BUCKET"

    image = Image(
        filename=file.filename or safe_name,
        stored_path=stored_name,
        album_id=album.id,
        user_id=current_user.id,
        status=final_status,
        steg_result=steg_result
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


@router.get("/{album_id}/images", response_model=list[ImageResponse])
def list_album_images(
    album_id: int,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    album = db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album no encontrado.")
    
    is_owner = bool(current_user and album.user_id == current_user.id)
    is_reviewer = bool(current_user and current_user.role in {"supervisor", "admin"})
    is_public_album = album.privacy == "public" and album.status == "approved"
    if not (is_owner or is_reviewer or is_public_album):
        raise HTTPException(status_code=403, detail="Acceso denegado.")

    query = db.query(Image).filter(Image.album_id == album_id)
    if not (is_owner or is_reviewer):
        query = query.filter(Image.status.in_(["CLEAN", "APPROVED_MANUAL"]))
    return query.order_by(Image.created_at.desc()).all()


@router.delete("/{album_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album_image(
    album_id: int,
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image = db.get(Image, image_id)
    if not image or image.album_id != album_id:
        raise HTTPException(status_code=404, detail="Imagen no encontrada.")
    
    if image.user_id != current_user.id and current_user.role not in {"supervisor", "admin"}:
        raise HTTPException(status_code=403, detail="No tienes permiso para borrar esta imagen.")
    
    # Determinar en qué bucket está
    bucket = "public" if image.status in ["CLEAN", "APPROVED_MANUAL"] else "quarantine"
    
    # Borrar de MinIO
    storage_service.delete_file(bucket, image.stored_path)
    
    # Borrar de DB
    db.delete(image)
    db.commit()
    return None
