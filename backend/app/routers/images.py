from pathlib import Path
from uuid import uuid4
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.album import Album
from app.models.image import Image
from app.models.user import User
from app.schemas.image import ImageResponse
from app.services.auth_service import get_current_user, get_optional_current_user
from app.services.image_processor import detect_mime_type, validate_and_process_image
from app.services.storage_service import storage_service
from app.services.steg_analyzer import analyze_image

router = APIRouter(prefix="/images", tags=["images"])
logger = logging.getLogger(__name__)


def _normalized(value: str | None) -> str:
    return (value or "").strip().lower()


@router.get("/{filename}")
async def get_image_file(
    filename: str,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Sirve el archivo de imagen directamente desde MinIO."""
    image = db.query(Image).filter(Image.stored_path == filename).first()
    if not image:
        # Intentamos buscar por el nombre original si el almacenado falla (fallback)
        image = db.query(Image).filter(Image.filename == filename).first()
        
    if not image:
        raise HTTPException(status_code=404, detail=f"Imagen {filename} no encontrada en DB.")
    
    album = db.get(Album, image.album_id)
    is_public_image = (
        image.status in ["CLEAN", "APPROVED_MANUAL"]
        and album is not None
        and _normalized(album.status) == "approved"
        and _normalized(album.privacy) == "public"
    )
    is_owner = bool(current_user and image.user_id == current_user.id)
    is_reviewer = bool(current_user and current_user.role in {"supervisor", "admin"})
    if not (is_public_image or is_owner or is_reviewer):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")

    try:
        # Determinar el bucket (por seguridad, si es PENDING solo el dueño o supervisor pueden verlo)
        bucket = "public"
        if image.status not in ["CLEAN", "APPROVED_MANUAL"]:
            bucket = "quarantine"
            
        # Verificar si el objeto existe en MinIO
        response = storage_service.client.get_object(
            storage_service.buckets[bucket],
            image.stored_path
        )
        
        from fastapi.responses import StreamingResponse
        # Intentar determinar el tipo de contenido por la extensión
        content_type = "image/jpeg"
        if image.filename.lower().endswith(".png"):
            content_type = "image/png"
        elif image.filename.lower().endswith(".gif"):
            content_type = "image/gif"
        elif image.filename.lower().endswith(".webp"):
            content_type = "image/webp"

        return StreamingResponse(response, media_type=content_type, headers={"X-Content-Type-Options": "nosniff"})
    except Exception as e:
        logger.error("Storage read failed for image id %s: %s", image.id, e)
        raise HTTPException(status_code=500, detail="Error de almacenamiento.")


@router.post("/upload", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    album_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    album = db.get(Album, album_id)
    if album is None or album.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album no encontrado.")
    if _normalized(album.status) != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo se pueden subir imagenes a albumes aprobados.",
        )
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande (maximo 10MB).")

    mime = detect_mime_type(file_content)
    if not mime or not mime.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Solo se permiten imagenes validas.")

    try:
        processed_content, processed_mime, extension = validate_and_process_image(file_content, file.filename or "")
        mime = processed_mime
        steg_result = analyze_image(processed_content, mime)
    except Exception as exc:
        logger.warning("Image processing failed; upload sent to quarantine: %s", exc)
        processed_content = file_content
        extension = Path(file.filename or "imagen").suffix.lower() or ".bin"
        steg_result = {"result": "ERROR", "is_suspicious": True, "error": "IMAGE_PROCESSING_FAILED"}

    safe_name = f"{uuid4().hex}{extension}"
    stored_name = storage_service.upload_to_quarantine(
        file_data=processed_content,
        file_name=safe_name,
        content_type=mime,
    )

    if not stored_name:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al subir la imagen al almacenamiento.")

    image = Image(
        filename=file.filename or safe_name,
        stored_path=stored_name,
        album_id=album.id,
        user_id=current_user.id,
        status="SUSPICIOUS" if steg_result.get("is_suspicious") else "CLEAN",
        steg_result=steg_result,
    )
    if image.status == "CLEAN" and not storage_service.move_object("quarantine", "public", stored_name):
        image.status = "SUSPICIOUS"
        image.steg_result = {
            **(image.steg_result or {}),
            "result": "SUSPICIOUS",
            "is_suspicious": True,
            "storage_alert": "COULD_NOT_PROMOTE_TO_PUBLIC_BUCKET",
        }
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


@router.get("/url/{image_id}")
@router.get("/{image_id}/url")
def get_image_url(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image = db.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagen no encontrada.")
    
    # Optional: check if user has access to the album
    album = db.get(Album, image.album_id)
    if (
        _normalized(album.privacy) == "private"
        and album.user_id != current_user.id
        and current_user.role not in {"supervisor", "admin"}
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para ver esta imagen.")

    bucket = "public" if image.status in ["CLEAN", "APPROVED_MANUAL"] else "quarantine"
    url = storage_service.get_presigned_url(bucket, image.stored_path)
    if not url:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al generar URL de la imagen.")
    
    return {"url": url}




