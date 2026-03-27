from fastapi import APIRouter

from app.api.v1 import auth, chat, events, favorites, reviews, routes, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(events.router)
api_router.include_router(reviews.router)
api_router.include_router(favorites.router)
api_router.include_router(routes.router)
api_router.include_router(chat.router)


@api_router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@api_router.get("/metrics")
def metrics() -> dict:
    from app.core.config import settings
    from app.core.metrics import REQUEST_COUNT

    if not settings.feature_flag_metrics:
        return {"enabled": False}
    return {"enabled": True, "requests_total": REQUEST_COUNT.get("n", 0)}
