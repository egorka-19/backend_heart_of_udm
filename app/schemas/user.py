import uuid

from pydantic import BaseModel, EmailStr


class UserMeOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    avatar_url: str | None = None
    category_user: str | None = None

    model_config = {"from_attributes": True}


class UserPatchRequest(BaseModel):
    username: str | None = None
    category_user: str | None = None
