from datetime import datetime
from pydantic import BaseModel


class ImageResponse(BaseModel):
    id: int
    original_filename: str
    stored_filename: str
    mime_type: str
    file_size: int
    status: str
    steg_result: dict | None = None
    album_id: int
    owner_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ImageReviewRequest(BaseModel):
    action: str   # "approve" | "reject"

    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in {"approve", "reject"}:
            raise ValueError("action must be 'approve' or 'reject'")
        return v


class QuarantineResponse(BaseModel):
    id: int
    original_filename: str
    stored_filename: str
    status: str
    steg_result: dict | None = None
    album_id: int
    owner_id: int
    created_at: datetime
    reviewed_at: datetime | None = None

    model_config = {"from_attributes": True}
