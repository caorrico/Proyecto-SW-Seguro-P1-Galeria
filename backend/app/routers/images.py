from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.album import Album
from app.models.image import Image
from app.models.user import User
from app.schemas.image import ImageResponse
from app.services.auth_service import get_current_user
from app.services.storage_service import storage_service

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/{filename:path}")
async def get_image_file(
    filename: str,
    db: Session = Depends(get_db)
):
    """Sirve el archivo de imagen directamente desde MinIO."""
    image = db.query(Image).filter(Image.stored_path == filename).first()
    if not image:
        # Intentamos buscar por el nombre original si el almacenado falla (fallback)
        image = db.query(Image).filter(Image.filename == filename).first()
        
    if not image:
        raise HTTPException(status_code=404, detail=f"Imagen {filename} no encontrada en DB.")
    
    try:
        # Determinar el bucket (por seguridad, si es PENDING solo el dueño o supervisor pueden verlo)
        bucket = "public"
        if image.status not in ["CLEAN", "APPROVED_MANUAL"]:
            bucket = "quarantine"
            # TODO: Añadir validación de sesión aquí si se desea restringir vista de cuarentena
            
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

        return StreamingResponse(response, media_type=content_type)
    except Exception as e:
        print(f"DEBUG: Error al leer de MinIO: {e}")
        raise HTTPException(status_code=500, detail=f"Error de almacenamiento: {str(e)}")


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
    if album.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo se pueden subir imagenes a albumes aprobados.",
        )
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Solo se permiten imagenes.")

    file_content = await file.read()
    safe_name = f"{uuid4().hex}_{Path(file.filename or 'imagen').name}"
    
    stored_name = storage_service.upload_file(
        file_data=file_content,
        file_name=safe_name,
        content_type=file.content_type
    )

    if not stored_name:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al subir la imagen al almacenamiento.")

    image = Image(
        filename=file.filename or safe_name,
        stored_path=stored_name,
        album_id=album.id,
        user_id=current_user.id,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


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
    if album.privacy == "private" and album.user_id != current_user.id and current_user.role != "supervisor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para ver esta imagen.")

    bucket = "public" if image.status in ["CLEAN", "APPROVED_MANUAL"] else "quarantine"
    url = storage_service.get_presigned_url(bucket, image.stored_path)
    if not url:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al generar URL de la imagen.")
    
    return {"url": url}




