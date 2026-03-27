from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserMeOut
from app.services.media import public_url_for_relative

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_me(user: User) -> UserMeOut:
    avatar = public_url_for_relative(user.avatar_path) if user.avatar_path else None
    return UserMeOut(
        id=user.id,
        email=user.email,
        username=user.username,
        avatar_url=avatar,
        category_user=user.category_user,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    exists = db.execute(select(User).where(User.email == str(payload.email))).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=str(payload.email).lower().strip(),
        username=payload.username.strip(),
        password_hash=security.hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access = security.create_access_token(str(user.id))
    refresh = security.create_refresh_token(str(user.id))
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=deps.expires_in_seconds(),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.execute(select(User).where(User.email == str(payload.email).lower().strip())).scalar_one_or_none()
    if user is None or not security.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access = security.create_access_token(str(user.id))
    refresh = security.create_refresh_token(str(user.id))
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=deps.expires_in_seconds(),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest) -> TokenResponse:
    try:
        data = security.decode_token_optional_type(payload.refresh_token, "refresh")
        sub = data.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        access = security.create_access_token(str(sub))
        new_refresh = security.create_refresh_token(str(sub))
        return TokenResponse(
            access_token=access,
            refresh_token=new_refresh,
            expires_in=deps.expires_in_seconds(),
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> None:
    return None


@router.get("/me", response_model=UserMeOut)
def auth_me(user: User = Depends(deps.get_current_user)) -> UserMeOut:
    return _user_me(user)
