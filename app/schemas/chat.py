import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChatClassifyRequest(BaseModel):
    messages: list[dict[str, str]] = Field(default_factory=list)


class ChatClassifyResponse(BaseModel):
    category_user: str


class ChatSessionOut(BaseModel):
    id: uuid.UUID


class ChatMessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class ChatMessageCreate(BaseModel):
    content: str
