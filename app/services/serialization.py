import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.review import Review
from app.schemas.event import EventOut
from app.services.media import public_url_for_relative


def batch_rating_stats(db: Session, event_ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[float, int]]:
    if not event_ids:
        return {}
    rows = db.execute(
        select(Review.event_id, func.avg(Review.rating), func.count(Review.id))
        .where(Review.event_id.in_(event_ids))
        .group_by(Review.event_id)
    ).all()
    out: dict[uuid.UUID, tuple[float, int]] = {}
    for eid, avg, cnt in rows:
        c = int(cnt or 0)
        if c == 0:
            out[eid] = (0.0, 0)
        else:
            out[eid] = (float(avg), c)
    for eid in event_ids:
        out.setdefault(eid, (0.0, 0))
    return out


def event_to_out(
    event: Event,
    *,
    rating_avg: float,
    review_count: int,
    is_favorite: bool,
) -> EventOut:
    img = public_url_for_relative(event.image_path) if event.image_path else None
    return EventOut(
        id=event.id,
        legacy_name=event.legacy_name,
        name=event.name,
        description=event.description,
        img_url=img,
        type=event.type,
        age=event.age,
        data=event.schedule,
        place=event.place,
        url=event.maps_url,
        schedule=event.schedule,
        status=event.status,
        rating_avg=round(rating_avg, 1),
        review_count=review_count,
        is_favorite=is_favorite,
    )
