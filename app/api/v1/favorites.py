import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app.models.event import Event
from app.models.favorite import Favorite
from app.models.user import User
from app.schemas.event import EventOut
from app.schemas.favorite import FavoriteEventOut
from app.services.event_query import get_event_rating_stats, user_favorite_event_ids
from app.services.serialization import event_to_out

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("", response_model=list[FavoriteEventOut])
def list_favorites(db: Session = Depends(get_db), user: User = Depends(deps.get_current_user)) -> list[FavoriteEventOut]:
    rows = db.execute(select(Favorite).where(Favorite.user_id == user.id)).scalars().all()
    out: list[FavoriteEventOut] = []
    fav_ids = user_favorite_event_ids(db, user.id)
    for fav in rows:
        ev = db.get(Event, fav.event_id)
        if ev is None:
            continue
        avg, cnt = get_event_rating_stats(db, ev.id)
        out.append(FavoriteEventOut(event=event_to_out(ev, rating_avg=avg, review_count=cnt, is_favorite=ev.id in fav_ids)))
    return out


@router.put("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_favorite(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(deps.get_current_user),
) -> None:
    if db.get(Event, event_id) is None:
        raise HTTPException(status_code=404, detail="Event not found")
    exists = db.execute(select(Favorite).where(Favorite.user_id == user.id, Favorite.event_id == event_id)).scalar_one_or_none()
    if exists:
        return None
    db.add(Favorite(user_id=user.id, event_id=event_id))
    db.commit()
    return None


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(deps.get_current_user),
) -> None:
    fav = db.execute(select(Favorite).where(Favorite.user_id == user.id, Favorite.event_id == event_id)).scalar_one_or_none()
    if fav:
        db.delete(fav)
        db.commit()
    return None
