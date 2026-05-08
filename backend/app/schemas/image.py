from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ImageResponse(BaseModel):
    id: int
    original_filename: str = Field(validation_alias="filename")
    stored_filename: str = Field(validation_alias="stored_path")
    album_id: int
    user_id: int
    status: str
    steg_result: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
