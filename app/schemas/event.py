import uuid

from pydantic import BaseModel


class EventCategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    sort_order: int

    model_config = {"from_attributes": True}


class EventOut(BaseModel):
    id: uuid.UUID
    legacy_name: str | None = None
    name: str
    description: str | None = None
    img_url: str | None = None
    type: str | None = None
    age: str | None = None
    data: str | None = None  # schedule alias for Android
    place: str | None = None
    url: str | None = None
    schedule: str | None = None
    status: str | None = None
    rating_avg: float = 0.0
    review_count: int = 0
    is_favorite: bool = False


class EventListOut(BaseModel):
    items: list[EventOut]
    total: int
    page: int
    page_size: int


class RatingOut(BaseModel):
    average: float
    count: int


class GalleryOut(BaseModel):
    urls: list[str]
