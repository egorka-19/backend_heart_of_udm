import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app.models.route import Route, RouteEvent
from app.models.user import User
from app.schemas.route import RouteDetailOut, RouteOut
from app.services.media import public_url_for_relative

router = APIRouter(prefix="/routes", tags=["routes"])


def _route_out(r: Route) -> RouteOut:
    img = public_url_for_relative(r.image_path) if r.image_path else None
    return RouteOut(
        id=r.id,
        name=r.name,
        description=r.description,
        image_url=img,
        category=r.category,
        goal=r.goal,
        days_range=r.days_range,
        people_count=r.people_count,
        duration=r.duration,
        difficulty=r.difficulty,
    )


@router.get("/recommended/me", response_model=RouteOut)
def recommended_me(db: Session = Depends(get_db), user: User = Depends(deps.get_current_user)) -> RouteOut:
    cat = user.category_user
    if not cat:
        raise HTTPException(status_code=404, detail="No user category; run classify first")
    r = db.execute(select(Route).where(Route.category == cat).order_by(Route.created_at.desc()).limit(1)).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="No routes for category")
    return _route_out(r)


@router.get("", response_model=list[RouteOut])
def list_routes(
    db: Session = Depends(get_db),
    category: str | None = Query(None),
    search: str | None = Query(None),
    goal: str | None = Query(None),
    days_range: str | None = Query(None),
    people_count: str | None = Query(None),
) -> list[RouteOut]:
    stmt = select(Route)
    if category:
        stmt = stmt.where(Route.category == category)
    if goal:
        stmt = stmt.where(Route.goal == goal)
    if days_range:
        stmt = stmt.where(Route.days_range == days_range)
    if people_count:
        stmt = stmt.where(Route.people_count == people_count)
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(func.lower(Route.name).like(like), func.lower(func.coalesce(Route.description, "")).like(like))
        )
    rows = db.execute(stmt.order_by(Route.name.asc())).scalars().all()
    return [_route_out(r) for r in rows]


@router.get("/{route_id}", response_model=RouteDetailOut)
def get_route(route_id: uuid.UUID, db: Session = Depends(get_db)) -> RouteDetailOut:
    r = db.get(Route, route_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Not found")
    evs = db.execute(
        select(RouteEvent.event_id).where(RouteEvent.route_id == route_id).order_by(RouteEvent.position.asc())
    ).scalars().all()
    base = _route_out(r)
    return RouteDetailOut(**base.model_dump(), event_ids=list(evs))
