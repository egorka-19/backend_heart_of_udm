import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app.models.event import Event, EventCategory
from app.models.review import Review, ReviewPhoto
from app.schemas.event import EventCategoryOut, EventListOut, EventOut, GalleryOut, RatingOut
from app.services.event_query import get_event_rating_stats, list_events_query, user_favorite_event_ids
from app.services.media import public_url_for_relative
from app.services.serialization import batch_rating_stats, event_to_out

router = APIRouter(tags=["events"])


@router.get("/event-categories", response_model=list[EventCategoryOut])
def list_categories(db: Session = Depends(get_db)) -> list[EventCategory]:
    rows = db.execute(select(EventCategory).order_by(EventCategory.sort_order.asc())).scalars().all()
    return list(rows)


@router.get("/events", response_model=EventListOut)
def list_events(
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(deps.get_current_user_optional_id),
    type: str | None = Query(None),
    search: str | None = Query(None),
    favorite_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> EventListOut:
    try:
        events, total = list_events_query(
            db,
            type_filter=type,
            search=search,
            favorite_only=favorite_only,
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Authentication required for favorite_only")

    fav_set: set[uuid.UUID] = set()
    if user_id is not None:
        fav_set = user_favorite_event_ids(db, user_id)

    ids = [e.id for e in events]
    stats = batch_rating_stats(db, ids)
    items: list[EventOut] = []
    for e in events:
        avg, cnt = stats.get(e.id, (0.0, 0))
        items.append(event_to_out(e, rating_avg=avg, review_count=cnt, is_favorite=e.id in fav_set))
    return EventListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/events/{event_id}", response_model=EventOut)
def get_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(deps.get_current_user_optional_id),
) -> EventOut:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    fav_set = user_favorite_event_ids(db, user_id) if user_id else set()
    avg, cnt = get_event_rating_stats(db, event.id)
    return event_to_out(event, rating_avg=avg, review_count=cnt, is_favorite=event.id in fav_set)


@router.get("/events/{event_id}/rating", response_model=RatingOut)
def get_rating(event_id: uuid.UUID, db: Session = Depends(get_db)) -> RatingOut:
    if db.get(Event, event_id) is None:
        raise HTTPException(status_code=404, detail="Event not found")
    avg, cnt = get_event_rating_stats(db, event_id)
    return RatingOut(average=round(avg, 1), count=cnt)


@router.get("/events/{event_id}/gallery", response_model=GalleryOut)
def get_gallery(event_id: uuid.UUID, db: Session = Depends(get_db)) -> GalleryOut:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    urls: list[str] = []
    if event.image_path:
        urls.append(public_url_for_relative(event.image_path))
    photos = db.execute(
        select(ReviewPhoto.file_path)
        .join(Review, Review.id == ReviewPhoto.review_id)
        .where(Review.event_id == event_id)
        .order_by(ReviewPhoto.created_at.asc())
    ).scalars().all()
    for p in photos:
        urls.append(public_url_for_relative(p))
    return GalleryOut(urls=urls)
