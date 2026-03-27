from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserMeOut, UserPatchRequest
from app.services.media import public_url_for_relative, save_upload_bytes

router = APIRouter(prefix="/users", tags=["users"])


def _me(user: User) -> UserMeOut:
    avatar = public_url_for_relative(user.avatar_path) if user.avatar_path else None
    return UserMeOut(
        id=user.id,
        email=user.email,
        username=user.username,
        avatar_url=avatar,
        category_user=user.category_user,
    )


@router.get("/me", response_model=UserMeOut)
def get_me(user: User = Depends(deps.get_current_user)) -> UserMeOut:
    return _me(user)


@router.patch("/me", response_model=UserMeOut)
def patch_me(
    payload: UserPatchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(deps.get_current_user),
) -> UserMeOut:
    if payload.username is not None:
        user.username = payload.username.strip()
    if payload.category_user is not None:
        user.category_user = payload.category_user.strip()
    db.add(user)
    db.commit()
    db.refresh(user)
    return _me(user)


@router.post("/me/avatar", response_model=UserMeOut)
async def upload_avatar(
    db: Session = Depends(get_db),
    user: User = Depends(deps.get_current_user),
    file: UploadFile = File(...),
) -> UserMeOut:
    rel = await save_upload_bytes(f"avatars/{user.id}", file, suffix=".jpg")
    user.avatar_path = rel
    db.add(user)
    db.commit()
    db.refresh(user)
    return _me(user)
