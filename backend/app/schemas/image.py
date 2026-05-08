from datetime import datetime

from pydantic import BaseModel


class ImageResponse(BaseModel):
    id: int
    filename: str
    album_id: int
    user_id: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
