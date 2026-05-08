from datetime import datetime
from pydantic import BaseModel, field_validator
import bleach


class AlbumCreateRequest(BaseModel):
    title: str
    description: str | None = None

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        v = bleach.clean(v.strip(), tags=[], strip=True)
        if len(v) < 3 or len(v) > 120:
            raise ValueError("title must be between 3 and 120 characters")
        return v

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # Eliminar cualquier HTML — previene Stored XSS
        return bleach.clean(v.strip(), tags=[], strip=True)


class AlbumResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    owner_id: int
    created_at: datetime
    reviewed_at: datetime | None = None

    model_config = {"from_attributes": True}


class AlbumReviewRequest(BaseModel):
    action: str   # "approve" | "reject"

    @field_validator("action")
    @classmethod
    def valid_action(cls, v: str) -> str:
        if v not in {"approve", "reject"}:
            raise ValueError("action must be 'approve' or 'reject'")
        return v
