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

router = APIRouter(prefix="/images", tags=["images"])
UPLOAD_DIR = Path("uploads")


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

    UPLOAD_DIR.mkdir(exist_ok=True)
    safe_name = f"{uuid4().hex}_{Path(file.filename or 'imagen').name}"
    stored_path = UPLOAD_DIR / safe_name
    stored_path.write_bytes(await file.read())

    image = Image(
        filename=file.filename or safe_name,
        stored_path=str(stored_path),
        album_id=album.id,
        user_id=current_user.id,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image
