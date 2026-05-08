from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.album import Album, AlbumStatus
from app.models.user import User
from app.routers.auth import get_current_user, require_supervisor
from app.schemas.album import AlbumCreateRequest, AlbumResponse, AlbumReviewRequest

router = APIRouter(prefix="/albums", tags=["Albums"])


# ── Helpers ───────────────────────────────────────────────────────────────
def _get_album_or_404(db: Session, album_id: int) -> Album:
    album = db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    return album


# ── User endpoints ────────────────────────────────────────────────────────
@router.post(
    "/request",
    response_model=AlbumResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request a new album (requires auth)",
)
def request_album(
    payload: AlbumCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    album = Album(
        title=payload.title,
        description=payload.description,
        status=AlbumStatus.pending,
        owner_id=current_user.id,
    )
    db.add(album)
    db.commit()
    db.refresh(album)
    return album


@router.get(
    "/my",
    response_model=list[AlbumResponse],
    summary="List current user's albums",
)
def my_albums(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Album)
        .filter(Album.owner_id == current_user.id)
        .order_by(Album.created_at.desc())
        .all()
    )


# ── Public endpoints ──────────────────────────────────────────────────────
@router.get(
    "/public",
    response_model=list[AlbumResponse],
    summary="List all approved albums (public)",
)
def public_albums(db: Session = Depends(get_db)):
    return (
        db.query(Album)
        .filter(Album.status == AlbumStatus.approved)
        .order_by(Album.created_at.desc())
        .all()
    )


# ── Supervisor endpoints ──────────────────────────────────────────────────
@router.get(
    "/pending",
    response_model=list[AlbumResponse],
    summary="List pending albums for review (supervisor only)",
)
def pending_albums(
    _: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    return (
        db.query(Album)
        .filter(Album.status == AlbumStatus.pending)
        .order_by(Album.created_at.asc())
        .all()
    )


@router.patch(
    "/{album_id}/review",
    response_model=AlbumResponse,
    summary="Approve or reject an album (supervisor only)",
)
def review_album(
    album_id: int,
    payload: AlbumReviewRequest,
    reviewer: User = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    album = _get_album_or_404(db, album_id)

    if album.status != AlbumStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only PENDING albums can be reviewed",
        )

    album.status = AlbumStatus.approved if payload.action == "approve" else AlbumStatus.rejected
    album.reviewer_id = reviewer.id
    album.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(album)
    return album
