import uuid

from pydantic import BaseModel, Field


class ReviewOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    avatar_url: str | None = None
    rating: int
    text: str
    date: str
    photo_urls: list[str] = []


class ReviewUpsertRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str
