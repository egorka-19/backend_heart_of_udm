import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

http_bearer = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> uuid.UUID:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = security.decode_token_optional_type(credentials.credentials, "access")
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token")
        return uuid.UUID(str(sub))
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user_optional_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> uuid.UUID | None:
    if credentials is None or not credentials.credentials:
        return None
    try:
        payload = security.decode_token_optional_type(credentials.credentials, "access")
        sub = payload.get("sub")
        if not sub:
            return None
        return uuid.UUID(str(sub))
    except (JWTError, ValueError):
        return None


def get_current_user(
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def expires_in_seconds() -> int:
    return settings.access_token_expire_minutes * 60
