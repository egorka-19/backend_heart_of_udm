import uuid

from pydantic import BaseModel


class RouteOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    image_url: str | None = None
    category: str | None = None
    goal: str | None = None
    days_range: str | None = None
    people_count: str | None = None
    duration: str | None = None
    difficulty: str | None = None


class RouteDetailOut(RouteOut):
    event_ids: list[uuid.UUID] = []
