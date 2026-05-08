from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.album import Album
from app.models.user import User
from app.schemas.album import AlbumCreate, AlbumRejectRequest, AlbumResponse, AlbumStatus
from app.services.auth_service import get_current_user, require_supervisor_or_admin

router = APIRouter(prefix="/albums", tags=["albums"])


def ensure_pending(album: Album) -> None:
    if album.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se pueden revisar albumes en estado pending.",
        )


@router.post("/request", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
def request_album(payload: AlbumCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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


@router.get("/supervisor", response_model=list[AlbumResponse])
def list_albums_for_review(
    status_filter: AlbumStatus | None = Query(default=None, alias="status"),
    _: User = Depends(require_supervisor_or_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Album)
    if status_filter:
        query = query.filter(Album.status == status_filter)
    return query.order_by(Album.created_at.desc()).all()


@router.patch("/{album_id}/approve", response_model=AlbumResponse)
def approve_album(
    album_id: int,
    reviewer: User = Depends(require_supervisor_or_admin),
    db: Session = Depends(get_db),
):
    album = db.get(Album, album_id)
    if album is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album no encontrado.")
    ensure_pending(album)
    album.status = "approved"
    album.reviewed_by = reviewer.id
    album.reviewed_at = datetime.utcnow()
    album.rejection_reason = None
    db.commit()
    db.refresh(album)
    return album


@router.patch("/{album_id}/reject", response_model=AlbumResponse)
def reject_album(
    album_id: int,
    payload: AlbumRejectRequest,
    reviewer: User = Depends(require_supervisor_or_admin),
    db: Session = Depends(get_db),
):
    album = db.get(Album, album_id)
    if album is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album no encontrado.")
    ensure_pending(album)
    album.status = "rejected"
    album.reviewed_by = reviewer.id
    album.reviewed_at = datetime.utcnow()
    album.rejection_reason = payload.rejection_reason
    db.commit()
    db.refresh(album)
    return album
