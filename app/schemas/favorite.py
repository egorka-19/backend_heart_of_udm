from pydantic import BaseModel

from app.schemas.event import EventOut


class FavoriteEventOut(BaseModel):
    event: EventOut
