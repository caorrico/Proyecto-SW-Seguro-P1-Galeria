import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


AlbumStatus = Literal["pending", "approved", "rejected"]
AlbumPrivacy = Literal["public", "private"]

DANGEROUS_TEXT_PATTERN = re.compile(
    r"(<\s*/?\s*script\b|javascript\s*:|onerror\s*=|onclick\s*=|onload\s*=|"
    r"<\s*iframe\b|<\s*object\b|<\s*embed\b|<\s*svg\b|<\s*img\b|data\s*:\s*text/html)",
    re.IGNORECASE,
)


def validate_safe_text(value: str, field_name: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"{field_name} no puede estar vacio.")
    if DANGEROUS_TEXT_PATTERN.search(normalized):
        raise ValueError(f"{field_name} contiene HTML o JavaScript no permitido.")
    return normalized


class AlbumCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=1, max_length=1000)
    privacy: AlbumPrivacy = "private"

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return validate_safe_text(value, "title")

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        return validate_safe_text(value, "description")


class AlbumRejectRequest(BaseModel):
    rejection_reason: str | None = Field(default=None, max_length=500)

    @field_validator("rejection_reason")
    @classmethod
    def validate_rejection_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_safe_text(value, "rejection_reason")


class AlbumResponse(BaseModel):
    id: int
    title: str
    description: str
    privacy: AlbumPrivacy
    status: AlbumStatus
    user_id: int
    created_at: datetime
    updated_at: datetime
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None

    model_config = {"from_attributes": True}
