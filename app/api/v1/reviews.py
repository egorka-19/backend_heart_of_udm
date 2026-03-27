import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app.models.event import Event
from app.models.review import Review, ReviewPhoto
from app.models.user import User
from app.schemas.review import ReviewOut, ReviewUpsertRequest
from app.services.media import public_url_for_relative, save_upload_bytes

router = APIRouter(tags=["reviews"])


def _fmt_date(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%d.%m.%y")


def _review_to_out(db: Session, r: Review) -> ReviewOut:
    user = db.get(User, r.user_id)
    uname = user.username if user else "Пользователь"
    avatar = public_url_for_relative(user.avatar_path) if user and user.avatar_path else None
    photos = db.execute(
        select(ReviewPhoto).where(ReviewPhoto.review_id == r.id).order_by(ReviewPhoto.sort_order.asc())
    ).scalars().all()
    photo_urls = [public_url_for_relative(p.file_path) for p in photos]
    return ReviewOut(
        id=r.id,
        user_id=r.user_id,
        user_name=uname,
        avatar_url=avatar,
        rating=r.rating,
        text=r.text,
        date=_fmt_date(r.created_at),
        photo_urls=photo_urls,
    )


@router.get("/events/{event_id}/reviews", response_model=list[ReviewOut])
def list_reviews(event_id: uuid.UUID, db: Session = Depends(get_db)) -> list[ReviewOut]:
    if db.get(Event, event_id) is None:
        raise HTTPException(status_code=404, detail="Event not found")
    reviews = db.execute(select(Review).where(Review.event_id == event_id).order_by(Review.created_at.desc())).scalars().all()
    return [_review_to_out(db, r) for r in reviews]


@router.put("/events/{event_id}/reviews/me", response_model=ReviewOut)
def upsert_my_review(
    event_id: uuid.UUID,
    payload: ReviewUpsertRequest,
    db: Session = Depends(get_db),
    user: User = Depends(deps.get_current_user),
) -> ReviewOut:
    if db.get(Event, event_id) is None:
        raise HTTPException(status_code=404, detail="Event not found")
    existing = db.execute(select(Review).where(Review.event_id == event_id, Review.user_id == user.id)).scalar_one_or_none()
    if existing is None:
        r = Review(user_id=user.id, event_id=event_id, rating=payload.rating, text=payload.text)
        db.add(r)
        db.commit()
        db.refresh(r)
        return _review_to_out(db, r)
    existing.rating = payload.rating
    existing.text = payload.text
    db.add(existing)
    db.commit()
    db.refresh(existing)
    return _review_to_out(db, existing)


@router.delete("/events/{event_id}/reviews/me", status_code=204)
def delete_my_review(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(deps.get_current_user),
) -> None:
    r = db.execute(select(Review).where(Review.event_id == event_id, Review.user_id == user.id)).scalar_one_or_none()
    if r is None:
        return None
    db.delete(r)
    db.commit()
    return None


@router.post("/events/{event_id}/reviews/me/photos", response_model=ReviewOut)
async def upload_review_photos(
    event_id: uuid.UUID,
    files: Annotated[list[UploadFile], File(description="Up to 3 images")],
    db: Session = Depends(get_db),
    user: User = Depends(deps.get_current_user),
) -> ReviewOut:
    if len(files) > 3:
        raise HTTPException(status_code=400, detail="Max 3 photos")
    if db.get(Event, event_id) is None:
        raise HTTPException(status_code=404, detail="Event not found")
    r = db.execute(select(Review).where(Review.event_id == event_id, Review.user_id == user.id)).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=400, detail="Create review first")
    current = db.execute(select(ReviewPhoto).where(ReviewPhoto.review_id == r.id)).scalars().all()
    if len(current) + len(files) > 3:
        raise HTTPException(status_code=400, detail="Max 3 photos total")
    max_order = max((p.sort_order for p in current), default=-1)
    for i, f in enumerate(files):
        rel = await save_upload_bytes(f"reviews/{r.id}", f, suffix=".jpg")
        p = ReviewPhoto(review_id=r.id, file_path=rel, sort_order=max_order + 1 + i)
        db.add(p)
    db.commit()
    db.refresh(r)
    return _review_to_out(db, r)


@router.delete("/review-photos/{photo_id}", status_code=204)
def delete_review_photo(
    photo_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(deps.get_current_user),
) -> None:
    photo = db.get(ReviewPhoto, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Not found")
    review = db.get(Review, photo.review_id)
    if review is None or review.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(photo)
    db.commit()
    return None
