import uuid
from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.favorite import Favorite
from app.models.review import Review


def get_event_rating_stats(db: Session, event_id: uuid.UUID) -> tuple[float, int]:
    row = db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(Review.event_id == event_id)
    ).one()
    avg, cnt = row[0], row[1] or 0
    if cnt == 0:
        return 0.0, 0
    return float(avg), int(cnt)


def user_favorite_event_ids(db: Session, user_id: uuid.UUID) -> set[uuid.UUID]:
    rows = db.execute(select(Favorite.event_id).where(Favorite.user_id == user_id)).scalars().all()
    return set(rows)


def list_events_query(
    db: Session,
    *,
    type_filter: str | None,
    search: str | None,
    favorite_only: bool,
    user_id: uuid.UUID | None,
    page: int,
    page_size: int,
) -> tuple[Sequence[Event], int]:
    stmt = select(Event)
    if type_filter:
        stmt = stmt.where(Event.type == type_filter)
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Event.name).like(like),
                func.lower(func.coalesce(Event.place, "")).like(like),
                func.lower(func.coalesce(Event.description, "")).like(like),
            )
        )
    if favorite_only:
        if user_id is None:
            raise ValueError("favorite_only_requires_auth")
        stmt = stmt.join(Favorite, Favorite.event_id == Event.id).where(Favorite.user_id == user_id)

    sub = stmt.subquery()
    total = int(db.scalar(select(func.count()).select_from(sub)) or 0)

    stmt = stmt.order_by(Event.name.asc()).offset((page - 1) * page_size).limit(page_size)
    events = db.execute(stmt).scalars().unique().all()
    return events, total
